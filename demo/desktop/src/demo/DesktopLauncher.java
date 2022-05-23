package demo;

import com.badlogic.gdx.backends.lwjgl3.Lwjgl3Application;
import com.badlogic.gdx.backends.lwjgl3.Lwjgl3ApplicationConfiguration;

import java.awt.*;

// Please note that on macOS your application needs to be started with the -XstartOnFirstThread JVM argument
public class DesktopLauncher {
    public static void main(String[] arg) {
        String type = arg[0];

        BaseDemo demo;

        if ("simple".equals(type)) {
            demo = new SimpleDemo();
        } else if ("shapekeys".equals(type)) {
            demo = new ShapekeysDemo();
        } else if ("skeleton".equals(type)) {
            demo = new SkeletonDemo();
        } else if ("animation".equals(type)) {
            demo = new AnimationDemo();
        } else if ("animation_shapekeys".equals(type)) {
            demo = new AnimationShapekeysDemo();
        } else if ("complex".equals(type)) {
            demo = new ComplexDemo();
        } else
            throw new IllegalArgumentException(type);

        Dimension screen = Toolkit.getDefaultToolkit().getScreenSize();
        int width = (int) (screen.width * 0.8f);
        int height = (int) (width * (9f / 16f));

        Lwjgl3ApplicationConfiguration config = new Lwjgl3ApplicationConfiguration();
        config.setTitle(type);
        config.setWindowedMode(width, height);

        new Lwjgl3Application(demo, config);
    }
}
