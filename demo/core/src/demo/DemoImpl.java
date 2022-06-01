package demo;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.BlendingAttribute;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.AnimationController;
import com.haz00.g3dmodelshape.ModelShape;
import com.haz00.g3dmodelshape.MeshShape;

public class DemoImpl extends BaseDemo {

    private ModelInstance inst;
    private AnimationController animCtl;
    private Node armatureNode;
    private MeshShape headShape, bodyShape;

    @Override
    public void create() {
        super.create();

        assets.load("suzanne.g3db", Model.class);
        assets.load("suzanne.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("suzanne.g3db", Model.class);
        model.getMaterial("tree").set(new BlendingAttribute());
        inst = new ModelInstance(model);

        animCtl = new AnimationController(inst);
        animCtl.setAnimation("SuzanneArmature|SuzanneAction", -1);
        armatureNode = inst.getNode("SuzanneArmature");

        ModelShape modelShape = assets.get("suzanne.shapes", ModelShape.class);

        headShape = modelShape.getShape("head mesh");
        headShape.setMesh(inst.getNode("head"));

        bodyShape = modelShape.getShape("body mesh");
        bodyShape.setMesh(inst.getNode("body"));
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
