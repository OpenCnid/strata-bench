"""Versioned monetary semantics, independent of provider-reported token counts.

USD-equivalent estimates are not invoices or subscription quota conversions.
All arithmetic is integer micro-USD, rounded up once per distinct request.
This module proves arithmetic, not ingress isolation or provider output limits.
"""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Digest, Positive, Ref, Strict, UInt
from .storage import digest, require


class TokenRates(Strict):
    # Micro-USD per million tokens; integer arithmetic also supports sub-micro rates.
    input: UInt
    cached_input: UInt
    cache_write: UInt
    output: UInt


class EstimateBasis(Strict):
    schema_: Literal["strata/ApiEquivalentEstimateBasis/1"] = Field(alias="schema")
    kind: Literal["api_equivalent_estimate"]
    provider: Literal["openai"]
    model: Literal["gpt-5.6-luna", "gpt-6-luna"]
    currency: Literal["USD"]
    price_sources: Annotated[list[str], Field(min_length=1)]
    price_date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    reference_tier: Literal["standard", "fast", "flex", "batch"]
    tier_policy: Literal["fixed_api_equivalent_not_subscription_tier"]
    regional_processing: Literal["none"]
    short_context: TokenRates
    long_context: TokenRates
    long_context_above_input_tokens: Positive
    context_window_tokens: Positive
    max_output_tokens: Positive
    cache_write_policy: Literal["explicit_subset_or_all_uncached_upper_bound"]
    reasoning_policy: Literal["included_in_output"]
    unknown_categories: Literal["block"]
    tool_charges: Literal["unsupported_block"]
    rounding: Literal["ceil_per_request_microusd"]

    @model_validator(mode="after")
    def valid_rates(self):
        for rate in (self.short_context, self.long_context):
            if not (rate.cache_write >= rate.input >= rate.cached_input and rate.output > 0):
                raise ValueError("invalid conservative rate ordering")
        if any(
            getattr(self.long_context, k) < getattr(self.short_context, k)
            for k in TokenRates.model_fields
        ):
            raise ValueError("long-context rates must bound short-context rates")
        if not self.long_context_above_input_tokens < self.context_window_tokens:
            raise ValueError("invalid context boundary")
        return self

    def fingerprint(self):
        return digest(self.model_dump())

    def estimate(self, usage):
        usage = TokenUsage.model_validate(usage)
        require(usage.model == self.model, "PRICE_MODEL_MISMATCH")
        rates = (
            self.long_context
            if usage.input_tokens > self.long_context_above_input_tokens
            else self.short_context
        )
        # Missing cache-write telemetry never implies zero writes. Charging the
        # uncached subset at the write rate is a labeled conservative estimate.
        writes = (
            usage.input_tokens - usage.cached_input_tokens
            if usage.cache_write_tokens is None
            else usage.cache_write_tokens
        )
        ordinary = usage.input_tokens - usage.cached_input_tokens - writes
        numerator = (
            ordinary * rates.input
            + usage.cached_input_tokens * rates.cached_input
            + writes * rates.cache_write
            + usage.output_tokens * rates.output
        )
        amount = (numerator + 999_999) // 1_000_000
        require(amount <= 2**53 - 1, "BUDGET_RANGE")
        return amount

    def maximum_request(self, *, max_input_tokens, max_output_tokens):
        require(
            type(max_input_tokens) is int
            and type(max_output_tokens) is int
            and 0 <= max_input_tokens <= self.context_window_tokens
            and 0 < max_output_tokens <= self.max_output_tokens,
            "EXPOSURE_RANGE",
        )
        return self.estimate(
            {
                "model": self.model,
                "input_tokens": max_input_tokens,
                "cached_input_tokens": 0,
                "cache_write_tokens": None,
                "output_tokens": max_output_tokens,
                "reasoning_tokens": None,
            }
        )


class TokenUsage(Strict):
    model: str
    input_tokens: UInt
    cached_input_tokens: UInt
    cache_write_tokens: UInt | None
    output_tokens: UInt
    reasoning_tokens: UInt | None

    @model_validator(mode="after")
    def subsets(self):
        if self.cached_input_tokens + (self.cache_write_tokens or 0) > self.input_tokens:
            raise ValueError("cache reads and writes must be disjoint input subsets")
        if self.reasoning_tokens is not None and self.reasoning_tokens > self.output_tokens:
            raise ValueError("reasoning must be an output subset")
        return self


class UsageValuation(Strict):
    schema_: Literal["strata/UsageValuation/1"] = Field(alias="schema")
    kind: Literal["api_equivalent_estimate", "actual_charge", "synthetic_fixture_units"]
    basis_digest: Digest
    raw_usage_ref: Ref
    usage: TokenUsage
    amount_microusd: UInt
    # Reported counters do not make the monetary estimate an actual charge.
    token_evidence: Literal["provider_reported", "synthetic_fixture"]


class FiniteExposure(Strict):
    schema_: Literal["strata/FiniteInferenceExposure/1"] = Field(alias="schema")
    basis_digest: Digest
    max_input_tokens: UInt
    max_output_tokens: Positive
    max_requests: Literal[1]
    input_bound_method: Literal["provider_context_limit", "qualified_token_count"]
    output_bound_method: Literal["provider_model_limit", "enforced_request_limit"]
    # The operator adapter must supply a real, profile-bound conformance record.
    # A timer or kill signal is deliberately not an accepted method.
    enforcement_ref: Ref

    def amount(self, basis):
        require(self.basis_digest == basis.fingerprint(), "ACCOUNTING_BASIS_MISMATCH")
        if self.input_bound_method == "provider_context_limit":
            require(self.max_input_tokens == basis.context_window_tokens, "EXPOSURE_RANGE")
        if self.output_bound_method == "provider_model_limit":
            require(self.max_output_tokens == basis.max_output_tokens, "EXPOSURE_RANGE")
        return basis.maximum_request(
            max_input_tokens=self.max_input_tokens, max_output_tokens=self.max_output_tokens
        )
