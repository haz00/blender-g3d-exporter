package demo;

import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.BlendingAttribute;
import com.haz00.g3dmodelshape.ModelShape;

public class SelectedDemo extends BaseDemo {

    private ModelInstance inst;
    // private AnimationController animCtl;
    // private Node armatureNode;

    @Override
    public void create() {
        super.create();

        assets.load("selected.g3dj", Model.class);
        assets.load("selected.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("selected.g3dj", Model.class);
        model.getMaterial("tree").set(new BlendingAttribute());
        inst = new ModelInstance(model);

//        ModelShape modelShape = assets.get("selected.shapes", ModelShape.class);

//        animCtl = new AnimationController(inst);
//        animCtl.setAnimation("", -1);
//        armatureNode = inst.getNode("");
    }

    @Override
    public void renderDemo() {
//        animCtl.update(Gdx.graphics.getDeltaTime());

        modelBatch.begin(cam);
        modelBatch.render(inst, env);
        modelBatch.end();

//        renderSkeleton(armatureNode, true, true, true, true);
    }
}
