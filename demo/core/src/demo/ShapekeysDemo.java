package demo;

import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.haz00.g3dmodelshape.ModelShape;
import com.haz00.g3dmodelshape.MeshShape;

public class ShapekeysDemo extends BaseDemo {

    private ModelInstance inst;
    private MeshShape rightShape;
    private MeshShape leftShape;
    private MeshShape backShape;
    private MeshShape forwardShape;

    @Override
    public void create() {
        super.create();

        assets.load("shapekeys.g3db", Model.class);
        assets.load("shapekeys.shapes", ModelShape.class);
        assets.finishLoading();

        Model model = assets.get("shapekeys.g3db", Model.class);
        inst = new ModelInstance(model);

        ModelShape modelShape = assets.get("shapekeys.shapes", ModelShape.class);

        // see demo.blend file for reference
        rightShape = modelShape.getShape("arrow R mesh");
        rightShape.setMesh(inst.getNode("arrow R"));

        leftShape = modelShape.getShape("arrow L mesh");
        leftShape.setMesh(inst.getNode("arrow L"));

        backShape = modelShape.getShape("arrow B mesh");
        backShape.setMesh(inst.getNode("arrow B"));

        forwardShape = modelShape.getShape("arrow F mesh");
        forwardShape.setMesh(inst.getNode("arrow F"));
    }

    @Override
    void renderDemo() {
        rightShape.setKey("Key 1", sin01());
        rightShape.calculate();

        leftShape.setKey("Key 1", sin01());
        leftShape.calculate();

        backShape.setKey("Key 1", sin01());
        backShape.setKey("Key 2", sin01());
        backShape.calculate();

        forwardShape.setKey("Key 1", sin01());
        forwardShape.setKey("Key 2", sin01());
        forwardShape.calculate();

        modelBatch.render(inst, env);
    }
}
