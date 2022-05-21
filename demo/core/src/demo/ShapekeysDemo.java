package demo;

import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.model.Node;
import haz00.modelshape.ModelShape;
import haz00.modelshape.NodeShape;

public class ShapekeysDemo extends BaseDemo {

    private ModelInstance inst;
    private NodeShape shape32;
    private NodeShape shape33;
    private NodeShape shape34;
    private NodeShape shape35;

    @Override
    public void create() {
        super.create();

        assets.load("shapekeys.g3dj", Model.class);
        assets.load("shapekeys.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("shapekeys.g3dj", Model.class);
        inst = new ModelInstance(model);

        ModelShape modelShape = assets.get("shapekeys.shapes", ModelShape.class);

        // see demo.blend file for reference
        Node node32 = inst.getNode("arrow.032");
        shape32 = modelShape.getShape(node32.id);
        shape32.setMesh(node32);
        shape32.setBasis("Basis");

        Node node33 = inst.getNode("arrow.033");
        shape33 = modelShape.getShape(node33.id);
        shape33.setMesh(node33);
        shape33.setBasis("Basis");

        Node node34 = inst.getNode("arrow.034");
        shape34 = modelShape.getShape(node34.id);
        shape34.setMesh(node34);
        shape34.setBasis("Basis");

        Node node35 = inst.getNode("arrow.035");
        shape35 = modelShape.getShape(node35.id);
        shape35.setMesh(node35);
        shape35.setBasis("Basis");
    }

    @Override
    void renderDemo() {
        shape32.setKey("Key 1", sin01());
        shape32.calculate();

        shape33.setKey("Key 1", sin01());
        shape33.calculate();

        shape34.setKey("Key 1", sin01());
        shape34.setKey("Key 2", sin01());
        shape34.calculate();

        shape35.setKey("Key 1", sin01());
        shape35.setKey("Key 2", sin01());
        shape35.calculate();

        modelBatch.render(inst, env);
    }
}
