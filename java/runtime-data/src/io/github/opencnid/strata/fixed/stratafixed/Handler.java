package io.github.opencnid.strata.fixed.stratafixed;

import io.github.opencnid.strata.fixed.Data;
import java.io.*;
import java.net.*;

/** HTTP-shaped responses to the exact existing consumers, entirely from RAM. */
public final class Handler extends URLStreamHandler {
    @Override protected URLConnection openConnection(URL url) throws IOException {
        byte[] bytes = Data.read(url.toExternalForm());
        System.err.println("STRATA_FIXED_DATA_READ/1 " + Data.ROUTES.get(url.toExternalForm()) + " " + Data.sha256(bytes));
        return new HttpURLConnection(url) {
            @Override public void connect() throws IOException {
                if (!method.equals("GET") || getDoOutput()) throw new IOException("FIXED_DATA_METHOD");
                connected = true;
            }
            @Override public int getResponseCode() throws IOException { connect(); return 200; }
            @Override public InputStream getInputStream() throws IOException {
                connect(); return new ByteArrayInputStream(bytes);
            }
            @Override public long getContentLengthLong() { return bytes.length; }
            @Override public int getContentLength() { return bytes.length; }
            @Override public boolean usingProxy() { return false; }
            @Override public void disconnect() { connected = false; }
        };
    }
    @Override protected URLConnection openConnection(URL url, Proxy proxy) throws IOException {
        if (proxy != Proxy.NO_PROXY) throw new IOException("FIXED_DATA_PROXY");
        return openConnection(url);
    }
}
