package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/** Bounded private loopback bridge. HTTP threads never read or mutate Minecraft objects. */
final class SettingsHttpBridge implements AutoCloseable {
    interface Dispatcher { JsonObject execute(JsonObject request) throws IOException; }
    interface Protocol {
        String path();
        String connectionSchema();
        JsonObject read(String text) throws IOException;
        void validate(JsonObject request, String session, long now) throws IOException;
        JsonObject response(JsonObject request, String session, String status, JsonObject result, String code);
        default boolean urgent(JsonObject request) { return false; }
    }
    private static final Protocol SETTINGS = new Protocol() {
        public String path() { return "/v1/settings"; }
        public String connectionSchema() { return "strata/NativeSettingsConnection/1"; }
        public JsonObject read(String text) throws IOException { return SettingsJson.read(text); }
        public void validate(JsonObject request, String session, long now) throws IOException {
            NativeSettingsProtocol.validate(request, session, now);
        }
        public JsonObject response(JsonObject request, String session, String status, JsonObject result, String code) {
            return NativeSettingsProtocol.response(request, session, status, result, code);
        }
    };
    static final int MAX_REQUEST = 32768, MAX_RESPONSE = 524288;
    private final Dispatcher dispatcher;
    private final Protocol protocol;
    private final HttpServer server;
    private final ThreadPoolExecutor executor;
    private final ScheduledThreadPoolExecutor watchdog;
    private final String session = UUID.randomUUID().toString();
    private final String token;
    private final Map<String, Job> jobs = new LinkedHashMap<>();
    private final ArrayBlockingQueue<Job> pending = new ArrayBlockingQueue<>(8);
    private final ArrayBlockingQueue<Job> urgent = new ArrayBlockingQueue<>(2);
    private volatile boolean closed;

    private static final class Job {
        final JsonObject request;
        final long expires;
        JsonObject response;
        boolean terminal;
        Job(JsonObject request, String session, long now, Protocol protocol) throws IOException {
            this.request = request.deepCopy();
            expires = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(
                SettingsJson.integer(request, "deadline_unix_ms") - now);
            response = protocol.response(request, session, "accepted", null, null);
        }
    }

    SettingsHttpBridge(Dispatcher dispatcher) throws IOException {
        this(dispatcher, SETTINGS);
    }

    SettingsHttpBridge(Dispatcher dispatcher, Protocol protocol) throws IOException {
        this.dispatcher = dispatcher;
        this.protocol = protocol;
        byte[] random = new byte[32];
        new SecureRandom().nextBytes(random);
        token = HexFormat.of().formatHex(random);
        server = HttpServer.create(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), 0), 16);
        executor = new ThreadPoolExecutor(2, 2, 0L, TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(16), task -> { Thread thread = new Thread(task, "strata-settings-http");
                thread.setDaemon(true); return thread; }, new ThreadPoolExecutor.AbortPolicy());
        watchdog = new ScheduledThreadPoolExecutor(1, task -> {
            Thread thread = new Thread(task, "strata-settings-http-watchdog"); thread.setDaemon(true); return thread;
        });
        watchdog.setRemoveOnCancelPolicy(true);
        server.setExecutor(executor);
        server.createContext(protocol.path(), this::handle);
        server.start();
    }

    JsonObject descriptor(String fingerprint) {
        JsonObject value = new JsonObject();
        value.addProperty("schema", protocol.connectionSchema());
        value.addProperty("host", "127.0.0.1");
        value.addProperty("port", server.getAddress().getPort());
        value.addProperty("session_id", session);
        value.addProperty("bearer_token", token);
        value.addProperty("fingerprint", fingerprint);
        value.addProperty("operator_development_only", true);
        return value;
    }

    private void handle(HttpExchange exchange) throws IOException {
        var timeout = watchdog.schedule(exchange::close, 3, TimeUnit.SECONDS);
        try {
            if (closed || exchange.getRequestHeaders().containsKey("Origin")
                    || !exchange.getRemoteAddress().getAddress().isLoopbackAddress()
                    || !("127.0.0.1:" + server.getAddress().getPort()).equals(exchange.getRequestHeaders().getFirst("Host"))) {
                reject(exchange, 403, "SETTINGS_FORBIDDEN"); return;
            }
            String authorization = exchange.getRequestHeaders().getFirst("Authorization");
            if (authorization == null || authorization.length() > 128 || !MessageDigest.isEqual(
                    ("Bearer " + token).getBytes(StandardCharsets.US_ASCII), authorization.getBytes(StandardCharsets.UTF_8))) {
                reject(exchange, 401, "SETTINGS_UNAUTHORIZED"); return;
            }
            String path = exchange.getRequestURI().getRawPath();
            if (exchange.getRequestURI().getRawQuery() != null) { reject(exchange, 400, "SETTINGS_ROUTE_INVALID"); return; }
            if (exchange.getRequestMethod().equals("POST") && path.equals(protocol.path())) {
                if (!"application/json".equals(exchange.getRequestHeaders().getFirst("Content-Type"))) {
                    reject(exchange, 415, "SETTINGS_CONTENT_TYPE"); return;
                }
                byte[] raw = exchange.getRequestBody().readNBytes(MAX_REQUEST + 1);
                if (raw.length > MAX_REQUEST) { reject(exchange, 413, "SETTINGS_REQUEST_TOO_LARGE"); return; }
                JsonObject request = protocol.read(StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw)).toString());
                long now = System.currentTimeMillis();
                protocol.validate(request, session, now);
                JsonObject response;
                synchronized (jobs) {
                    String id = SettingsJson.string(request, "request_id");
                    Job existing = jobs.get(id);
                    if (existing != null) {
                        if (!existing.request.equals(request)) throw new IOException("SETTINGS_IDEMPOTENCY_CONFLICT");
                        response = existing.response.deepCopy();
                    } else {
                        ArrayBlockingQueue<Job> queue = protocol.urgent(request) ? urgent : pending;
                        if (queue.remainingCapacity() == 0) throw new IOException("SETTINGS_QUEUE_FULL");
                        if (jobs.size() >= 64) {
                            var iterator = jobs.entrySet().iterator();
                            while (jobs.size() >= 64 && iterator.hasNext()) {
                                if (iterator.next().getValue().terminal) iterator.remove();
                            }
                        }
                        if (jobs.size() >= 64) throw new IOException("SETTINGS_QUEUE_FULL");
                        Job job = new Job(request, session, now, protocol);
                        jobs.put(id, job);
                        queue.add(job);
                        response = job.response.deepCopy();
                    }
                }
                send(exchange, "accepted".equals(response.get("status").getAsString()) ? 202 : 200, response);
            } else if (exchange.getRequestMethod().equals("GET") && path.startsWith(protocol.path() + "/")) {
                String id = path.substring(protocol.path().length() + 1);
                NativeSettingsProtocol.identifier(id);
                JsonObject response;
                synchronized (jobs) {
                    Job job = jobs.get(id);
                    response = job == null ? null : job.response.deepCopy();
                }
                if (response == null) { reject(exchange, 404, "SETTINGS_REQUEST_UNKNOWN"); return; }
                send(exchange, "accepted".equals(response.get("status").getAsString()) ? 202 : 200, response);
            } else reject(exchange, 405, "SETTINGS_ROUTE_INVALID");
        } catch (IOException | RuntimeException error) {
            String code = error.getMessage();
            reject(exchange, 400, code != null && code.matches("[A-Z][A-Z0-9_]{1,95}") ? code : "SETTINGS_REQUEST_INVALID");
        } finally { timeout.cancel(false); exchange.close(); }
    }

    /** Called only by the owning client thread; at most one operation per tick. */
    void drain() {
        if (closed) return;
        Job job = urgent.poll();
        if (job == null) job = pending.poll();
        if (job == null) return;
        JsonObject response;
        try {
            if (System.nanoTime() >= job.expires) throw new IOException("SETTINGS_DEADLINE_EXPIRED");
            protocol.validate(job.request, session, System.currentTimeMillis());
            JsonObject result = dispatcher.execute(job.request.deepCopy());
            response = protocol.response(job.request, session, "completed", result, null);
            if (response.toString().getBytes(StandardCharsets.UTF_8).length > MAX_RESPONSE) throw new IOException("SETTINGS_RESPONSE_TOO_LARGE");
        } catch (IOException | RuntimeException error) {
            String code = error.getMessage();
            response = protocol.response(job.request, session, "failed", null,
                code != null && code.matches("[A-Z][A-Z0-9_]{1,95}") ? code : "SETTINGS_EXECUTION_FAILED");
        }
        synchronized (jobs) { job.response = response; job.terminal = true; }
    }

    private static void reject(HttpExchange exchange, int status, String code) throws IOException {
        JsonObject value = new JsonObject(); value.addProperty("error_code", code); send(exchange, status, value);
    }

    private static void send(HttpExchange exchange, int status, JsonObject value) throws IOException {
        byte[] bytes = value.toString().getBytes(StandardCharsets.UTF_8);
        if (bytes.length > MAX_RESPONSE) throw new IOException("SETTINGS_RESPONSE_TOO_LARGE");
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.getResponseHeaders().set("Cache-Control", "no-store");
        exchange.sendResponseHeaders(status, bytes.length);
        exchange.getResponseBody().write(bytes);
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        server.stop(0);
        executor.shutdownNow();
        watchdog.shutdownNow();
        pending.clear();
        urgent.clear();
    }
}
