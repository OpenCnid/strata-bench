/** Shared, dependency-free sanitized errors; safe to ship with the scoped client. */
export class Fault extends Error {
  constructor(readonly code: string) { super(code); }
}
export function requireThat(test: unknown, code: string): asserts test {
  if (!test) throw new Fault(code);
}
export function errorBody(error: unknown, requestId: string | null, epoch: number | null) {
  const code = error instanceof Fault ? error.code : 'INTERNAL_ERROR';
  return {code, message:code, retryable:false, retry_after_ms:null,
    request_id:requestId, expected_epoch:epoch, details_ref:null};
}
