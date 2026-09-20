import java.nio.file.Files;
import java.nio.file.Path;

/** Disposable lifetime test. No Minecraft, windows, input, networking or credentials. */
class DesktopLifetimeFixture {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of(args[0]), "ready");
        Thread.sleep(60000);
        Files.writeString(Path.of(args[0] + ".late"), "unexpected late effect");
    }
}
