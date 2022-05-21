package demo;

import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.model.Node;

public class SkeletonDemo extends BaseDemo{

    private ModelInstance inst;
    private Node armatureNode;

    @Override
    public void create() {
        super.create();

        assets.load("skeleton.g3dj", Model.class);
        assets.finishLoading();

        Model model = assets.get("skeleton.g3dj", Model.class);
        inst = new ModelInstance(model);

        armatureNode = inst.getNode("Armature");
    }

    @Override
    public void renderDemo() {
        modelBatch.begin(cam);
        modelBatch.render(inst, env);
        modelBatch.end();

        renderSkeleton(armatureNode, true, true, true, true);
    }
}
