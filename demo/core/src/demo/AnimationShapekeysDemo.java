package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;
import com.haz00.g3dmodelshape.ModelShape;
import com.haz00.g3dmodelshape.MeshShape;

public class AnimationShapekeysDemo extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;
    private MeshShape shape;

    @Override
    public void create() {
        super.create();

        assets.load("animation and shapekeys.g3db", Model.class);
        assets.load("animation and shapekeys.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("animation and shapekeys.g3db", Model.class);
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("ArmatureAnim.001|AnimAction", -1);
        armatureNode = inst.getNode("ArmatureAnim.001");

        ModelShape modelShape = assets.get("animation and shapekeys.shapes", ModelShape.class);

        shape = modelShape.getShape("anim+shapekeys mesh");
        shape.setMesh(inst.getNode("anim+shapekeys"));
    }

    @Override
    public void renderDemo() {
        shape.setKey("Key 1", sin01());
        shape.setKey("Key 2", sin01());
        shape.calculate();

        animCtl.update(Gdx.graphics.getDeltaTime());

        modelBatch.begin(cam);
        modelBatch.render(inst, env);
        modelBatch.end();

        renderSkeleton(armatureNode, true, true, true, true);
    }
}
