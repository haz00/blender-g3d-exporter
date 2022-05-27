package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;

public class AnimationDemo extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;

    @Override
    public void create() {
        super.create();

        assets.load("animation.g3dj", Model.class);
        assets.finishLoading();

        Model model = assets.get("animation.g3dj", Model.class);
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("ArmatureAnim|AnimAction", -1);
        armatureNode = inst.getNode("ArmatureAnim");
    }

    @Override
    public void renderDemo() {
        animCtl.update(Gdx.graphics.getDeltaTime());

        modelBatch.begin(cam);
        modelBatch.render(inst, env);
        modelBatch.end();

        renderSkeleton(armatureNode, true, true, true, true);
    }
}
