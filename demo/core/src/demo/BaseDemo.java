package demo;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.Input;
import com.badlogic.gdx.InputMultiplexer;
import com.badlogic.gdx.assets.AssetManager;
import com.badlogic.gdx.graphics.Color;
import com.badlogic.gdx.graphics.GL20;
import com.badlogic.gdx.graphics.PerspectiveCamera;
import com.badlogic.gdx.graphics.g2d.BitmapFont;
import com.badlogic.gdx.graphics.g2d.SpriteBatch;
import com.badlogic.gdx.graphics.g3d.*;
import com.badlogic.gdx.graphics.g3d.attributes.BlendingAttribute;
import com.badlogic.gdx.graphics.g3d.attributes.DepthTestAttribute;
import com.badlogic.gdx.graphics.g3d.environment.DirectionalLight;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.utils.CameraInputController;
import com.badlogic.gdx.graphics.g3d.utils.ModelBuilder;
import com.badlogic.gdx.graphics.glutils.ShapeRenderer;
import com.badlogic.gdx.math.Matrix4;
import com.badlogic.gdx.math.Vector3;
import com.badlogic.gdx.scenes.scene2d.Stage;
import com.badlogic.gdx.scenes.scene2d.ui.Skin;
import com.badlogic.gdx.utils.ScreenUtils;
import com.badlogic.gdx.utils.viewport.ScreenViewport;

import static com.badlogic.gdx.graphics.VertexAttributes.Usage.ColorPacked;
import static com.badlogic.gdx.graphics.VertexAttributes.Usage.Position;
import static com.badlogic.gdx.graphics.g3d.attributes.ColorAttribute.createAmbientLight;
import static com.badlogic.gdx.graphics.g3d.attributes.ColorAttribute.createDiffuse;
import static com.badlogic.gdx.math.MathUtils.degRad;
import static com.badlogic.gdx.math.MathUtils.sin;

/**
 * Encapsulates boilerplate stuff - nothing to read here
 */
public abstract class BaseDemo extends ApplicationAdapter {

    float totalTime = 0;

    Stage stage;
    Skin skin;

    BitmapFont font;

    ModelBatch modelBatch;
    SpriteBatch spriteBatch;
    ShapeRenderer shapeRenderer;

    Environment env;
    DirectionalLight light;

    PerspectiveCamera cam;
    CameraInputController camCtl;

    Model gridModel;
    ModelInstance grid;

    AssetManager assets;

    Model axesBoneModel;
    ModelInstance xyzBone;
    Model boneModel;
    ModelInstance bone;
    boolean skeletonVisible = true;

    @Override
    public void create() {
        assets = new AssetManager();

        font = new BitmapFont();

        light = new DirectionalLight();
        light.setColor(Color.WHITE);
        light.setDirection(-0.707f, -0.707f, -0.707f);

        env = new Environment();
        env.set(createAmbientLight(0.5f, 0.5f, 0.5f, 1));
        env.add(light);

        cam = new PerspectiveCamera(45, Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
        cam.near = 0.01f;
        cam.far = 1000;
        cam.position.set(5, 5, 5);
        cam.lookAt(Vector3.Zero);
        cam.update();

        camCtl = new CameraInputController(cam);

        modelBatch = new ModelBatch();
        spriteBatch = new SpriteBatch();
        shapeRenderer = new ShapeRenderer();

        ModelBuilder builder = new ModelBuilder();

        boneModel = builder.createBox(1, 1, 1,
                new Material(createDiffuse(0, 1, 0, 0.5f), new BlendingAttribute())
                , Position);
        bone = new ModelInstance(boneModel);

        axesBoneModel = builder.createXYZCoordinates(0.15f, 0.1f, 0.25f, 5, GL20.GL_TRIANGLES,
                new Material(new DepthTestAttribute(GL20.GL_ALWAYS, 1, 0.01f))
                , Position | ColorPacked);
        xyzBone = new ModelInstance(axesBoneModel);

        gridModel = builder.createLineGrid(20, 20, 1, 1,
                new Material(createDiffuse(0, 0, 0, 0.2f), new BlendingAttribute())
                , Position);

        grid = new ModelInstance(gridModel);

        assets.load("skin/uiskin.json", Skin.class);
        assets.finishLoading();

        skin = assets.get("skin/uiskin.json", Skin.class);

        stage = new Stage(new ScreenViewport());
        Gdx.input.setInputProcessor(new InputMultiplexer(stage, camCtl));
    }

    @Override
    public void render() {
        totalTime += Gdx.graphics.getDeltaTime();
        camCtl.update();

        if (Gdx.input.isKeyJustPressed(Input.Keys.SPACE))
            skeletonVisible = !skeletonVisible;

        ScreenUtils.clear(0.95f, 0.95f, 0.95f, 1, true);

        modelBatch.begin(cam);
        modelBatch.render(grid);
        modelBatch.end();

        renderDemo();

        stage.act();
        stage.draw();
    }

    abstract void renderDemo();

    void renderSkeleton(Node armature, boolean bones, boolean axes, boolean names, boolean relations) {
        // ugly hardcode implemented for this demo purposes only

        if (!skeletonVisible)
            return;

        Gdx.gl.glClear(GL20.GL_DEPTH_BUFFER_BIT);

        shapeRenderer.setProjectionMatrix(cam.combined);
        shapeRenderer.begin(ShapeRenderer.ShapeType.Line);
        modelBatch.begin(cam);
        for (Node bone : armature.getChildren()) {
            drawBone(armature, bone, bones, axes, false, relations);
        }
        modelBatch.end();
        shapeRenderer.end();

        spriteBatch.setProjectionMatrix(stage.getViewport().getCamera().combined);
        spriteBatch.begin();
        for (Node bone : armature.getChildren()) {
            drawBone(armature, bone, false, false, names, false);
        }
        spriteBatch.end();
    }

    void drawBone(Node armature, Node bone, boolean bones, boolean axes, boolean names, boolean relations) {
        if (bone == null)
            return;

        Node parent = bone.getParent();

        if (axes) {
            xyzBone.transform.set(bone.globalTransform);
            modelBatch.render(xyzBone);
        }

        if (names) {
            Vector3 screen = cam.project(bone.globalTransform.getTranslation(new Vector3()));
            font.draw(spriteBatch, bone.id, screen.x, screen.y);
        }

        if (parent != null && parent != armature) {

            if (bones) {
                Matrix4 boneRenderLocal = new Matrix4()
                        .setToScaling(0.1f, bone.translation.y, 0.1f)
                        .setTranslation(bone.translation.cpy().scl(0.5f));

                this.bone.transform
                        .set(parent.globalTransform)
                        .mul(boneRenderLocal);

                modelBatch.render(this.bone);
            }

            if (relations) {
                Vector3 parentHead = parent.globalTransform.getTranslation(new Vector3());
                Vector3 head = bone.globalTransform.getTranslation(new Vector3());

                shapeRenderer.setColor(Color.YELLOW);
                shapeRenderer.line(parentHead, head);
            }
        }

        for (Node child : bone.getChildren()) {
            drawBone(armature, child, bones, axes, names, relations);
        }
    }

    float sin01() {
        return (sin(totalTime * 180 * degRad) + 1) / 2;
    }

    @Override
    public void resize(int width, int height) {
        float ratio = (float) width / height;

        if (ratio >= 1) {
            cam.viewportWidth = width;
            cam.viewportHeight = (float) width / ratio;
        } else {
            cam.viewportHeight = height;
            cam.viewportWidth = (float) height * ratio;
        }

        cam.update();

        stage.getViewport().update(width, height, true);
    }

    @Override
    public void dispose() {
        spriteBatch.dispose();
        modelBatch.dispose();
        shapeRenderer.dispose();
        assets.dispose();
        font.dispose();
        stage.dispose();
        gridModel.dispose();
        boneModel.dispose();
        axesBoneModel.dispose();
    }
}
