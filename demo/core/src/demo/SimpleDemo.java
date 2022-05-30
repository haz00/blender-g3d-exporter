package demo;

import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;

public class SimpleDemo extends BaseDemo {

    private ModelInstance inst;

    @Override
    public void create() {
        super.create();

        assets.load("simple.g3db", Model.class);
        assets.finishLoading();

        Model model = assets.get("simple.g3db", Model.class);
        inst = new ModelInstance(model);
    }

    @Override
    public void renderDemo() {
        modelBatch.render(inst, env);
    }
}
