package io.github.opencnid.strata.telemetry;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/** Actual process and production clock; synthetic callbacks, no Minecraft. */
public final class LiveClockFixture {
    public static void main(String[] args) throws Exception {
        var clock = new ServerClock();
        var reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String command;
        while ((command = reader.readLine()) != null) {
            if (command.equals("stop")) {
                System.out.println(clock.stop());
                return;
            }
            if (!command.equals("connected") && !command.equals("disconnected"))
                throw new IllegalArgumentException("fixture command");
            clock.startTick();
            if (command.equals("connected"))
                clock.avatarTick(UUID.fromString("11111111-1111-1111-1111-111111111111"));
            clock.endTick();
            System.out.println(clock.sample());
        }
        throw new IllegalStateException("fixture stop missing");
    }
}
