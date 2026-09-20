package io.github.opencnid.strata.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Matrix4f;
import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.network.chat.Component;

/** Copies only operands passed to the pinned normal header drawing helper. */
final class JeiHeaderCopies {
    static GameRecipeHeaders.Label copy(String kind, PoseStack pose, Font font, Object text, Object area,
                                         GameRecipeRenderCapture.Key key) throws IOException {
        if (pose == null || font != Minecraft.getInstance().font || area == null
                || !area.getClass().getName().equals("mezz.jei.common.util.ImmutableRect2i")) throw invalid();
        var identity = new Matrix4f(); identity.setIdentity();
        if (!pose.last().pose().equals(identity)) throw invalid();
        var box = new GameRecipeSlots.Rect(number(area,"getX"), number(area,"getY"), number(area,"getWidth"), number(area,"getHeight"));
        return GameRecipeHeaders.clippedCopy(kind, new GameRecipeSlots.Rect(0, 0, key.width(), key.height()), box, () -> {
            // This reader runs only after geometry permits the actual draw operand.
            String value; int width;
            if (kind.equals("category") && text instanceof Component component) {
                try { value = NativeQuests.plain(component); }
                catch (NativeQuests.UnsupportedText unsupported) {
                    return new GameRecipeHeaders.Measured(new GameRecipeHeaders.Label(kind, "unsupported", null), 0);
                }
                GameQuestText.bounded(value, 1024); width = font.width(component);
            } else if (kind.equals("page") && text instanceof String string) {
                value = string; GameQuestText.bounded(value, 1024); width = font.width(string);
            } else throw invalid();
            return new GameRecipeHeaders.Measured(new GameRecipeHeaders.Label(kind, "text", value), width);
        });
    }
    private static int number(Object area, String name) throws IOException {
        Object value = NativeQuests.call(area, name); if (!(value instanceof Integer number)) throw invalid(); return number;
    }
    private static IOException invalid() { return new IOException("GAME_RECIPE_HEADER_INVALID"); }
}
