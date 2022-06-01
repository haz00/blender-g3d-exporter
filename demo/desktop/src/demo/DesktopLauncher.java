package demo;

import com.badlogic.gdx.backends.lwjgl3.Lwjgl3Application;
import com.badlogic.gdx.backends.lwjgl3.Lwjgl3ApplicationConfiguration;

import java.awt.*;

// Please note that on macOS your application needs to be started with the -XstartOnFirstThread JVM argument
public class DesktopLauncher {
    public static void main(String[] arg) {
        int width = (int) (Toolkit.getDefaultToolkit().getScreenSize().width * 0.8f);
        int height = (int) (width * (9f / 16f));

        Lwjgl3ApplicationConfiguration config = new Lwjgl3ApplicationConfiguration();
        config.setTitle("Demo");
        config.setWindowedMode(width, height);

        new Lwjgl3Application(new DemoImpl(), config);
    }
}
