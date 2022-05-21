package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.BlendingAttribute;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;
import haz00.modelshape.ModelShape;
import haz00.modelshape.NodeShape;

public class ComplexDemo extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;
    private NodeShape headShape, bodyShape;

    @Override
    public void create() {
        super.create();

        assets.load("complex.g3dj", Model.class);
        assets.load("complex.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("complex.g3dj", Model.class);
        model.getMaterial("tree").set(new BlendingAttribute());
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("Armature.002|complex", -1);
        armatureNode = inst.getNode("Armature.002");

        ModelShape modelShape = assets.get("complex.shapes", ModelShape.class);

        Node head = inst.getNode("Head");
        headShape = modelShape.getShape(head.id);
        headShape.setMesh(head);
        headShape.setBasis("Basis");

        Node body = inst.getNode("Body");
        bodyShape = modelShape.getShape(body.id);
        bodyShape.setMesh(body);
        bodyShape.setBasis("Basis");
    }

    @Override
    public void renderDemo() {
        headShape.setKey("Key 1", sin01());
        headShape.calculate();

        bodyShape.setKey("Key 1", sin01());
        bodyShape.calculate();

        animCtl.update(Gdx.graphics.getDeltaTime());

        modelBatch.begin(cam);
        modelBatch.render(inst, env);
        modelBatch.end();

        renderSkeleton(armatureNode, true, true, true, true);
    }
}
