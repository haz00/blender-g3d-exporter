package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;
import haz00.modelshape.ModelShape;
import haz00.modelshape.NodeShape;

public class AnimationShapekeysDemo extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;
    private NodeShape shape;

    @Override
    public void create() {
        super.create();

        assets.load("animation and shapekeys.g3dj", Model.class);
        assets.load("animation and shapekeys.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("animation and shapekeys.g3dj", Model.class);
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("Armature.001|Armature.004Action", -1);
        armatureNode = inst.getNode("Armature.001");

        ModelShape modelShape = assets.get("animation and shapekeys.shapes", ModelShape.class);

        Node node37 = inst.getNode("arrow.037");
        shape = modelShape.getShape(node37.id);
        shape.setMesh(node37);
        shape.setBasis("Basis");
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
