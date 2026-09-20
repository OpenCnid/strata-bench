package io.github.opencnid.strata.client;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

/** Disposable OS process fixture. No Minecraft initialization, account or desktop. */
public final class ProcessGuardFixture {
    public static void main(String[] args) throws Exception {
        if (args.length == 2 && args[0].equals("child")) {
            Path marker = Path.of(args[1]);
            Files.writeString(Path.of(args[1] + ".ready"), "synthetic child ready");
            Thread.sleep(2000);
            Files.writeString(marker, "late synthetic effect");
            Thread.sleep(60000);
            return;
        }
        System.out.println("ready");
        System.out.flush();
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in));
        for (String line; (line = input.readLine()) != null;) {
            if (line.equals("hang")) {
                System.out.println("hung");
                System.out.flush();
                Thread.sleep(60000);
            } else if (line.startsWith("spawn ")) {
                Process child = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin", "java.exe").toString(),
                        "-cp", System.getProperty("java.class.path"), ProcessGuardFixture.class.getName(),
                        "child", line.substring(6)).start();
                System.out.println(child.pid());
                System.out.flush();
            } else if (line.equals("stop")) {
                return;
            } else {
                throw new IllegalArgumentException("TEST_INPUT_INVALID");
            }
        }
    }
}
