package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.BlendingAttribute;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;

public class DemoImpl extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;

    @Override
    public void create() {
        super.create();

        assets.load("demo.g3db", Model.class);
        assets.finishLoading();

        Model model = assets.get("demo.g3db", Model.class);
        model.getMaterial("tree").set(new BlendingAttribute());
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("SuzanneArmature|SuzanneAction", -1);
        armatureNode = inst.getNode("SuzanneArmature");
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
