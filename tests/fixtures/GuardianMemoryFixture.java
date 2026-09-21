import java.io.BufferedReader;
import java.io.InputStreamReader;

/** Disposable operator fixture: no Minecraft, windows, networking or credentials. */
public final class GuardianMemoryFixture {
    private static volatile byte[][] retained;

    public static void main(String[] args) throws Exception {
        int mib = Integer.parseInt(args[0]);
        if (args.length != 1 || mib < 16 || mib > 3072 || mib % 16 != 0) {
            throw new IllegalArgumentException("bounded allocation required");
        }
        var input = new BufferedReader(new InputStreamReader(System.in));
        System.out.println("ready " + ProcessHandle.current().pid());
        if (!"allocate".equals(input.readLine())) throw new IllegalStateException("not armed");
        retained = new byte[mib / 16][];
        for (int i = 0; i < retained.length; i++) {
            byte[] block = new byte[16 * 1024 * 1024];
            for (int j = 0; j < block.length; j += 4096) block[j] = 1;
            block[block.length - 1] = 1;
            retained[i] = block;
        }
        System.out.println("allocated " + mib);
        // Strong references survive until the guardian kills this disposable JVM.
        // EOF also exits; no shutdown hook hides or defers process termination.
        input.readLine();
    }
}
