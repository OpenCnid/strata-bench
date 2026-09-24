import io.github.opencnid.strata.vanillaclock.Clock;
import java.util.UUID;

/** Explicit synthetic callbacks; this fixture never launches Minecraft. */
public class CallbackTest {
    public static void main(String[] args) throws Exception {
        if (Clock.class.getClassLoader() != null) throw new AssertionError("not bootstrap visible");
        Clock.bound("net/minecraft/server/MinecraftServer",
            "bb6ab22cbdff49b8f7a76523a21ed54166244b914d63064d1a30f2e1747f802f", "a".repeat(64));
        Clock.bound("agh", "cc6a79060c45ab954bcf80a301b8a21ed48b43fee9eb29ab4a13b28c93b10ad2", "b".repeat(64));
        Clock.start(); Thread.sleep(200); Clock.tickStart();
        Clock.avatar(UUID.fromString("12345678-1234-1234-1234-123456789abc"));
        Thread.sleep(5); Clock.tickEnd(); Clock.stop();
    }
}
