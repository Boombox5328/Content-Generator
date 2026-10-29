import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "blocky"))
import video, spec, runner

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        runner.preview(video.frame, spec.FPS, sys.argv[2], [float(x) for x in sys.argv[3:]])
    else:
        runner.render_video(video.frame, int(spec.DUR * spec.FPS), spec.FPS, sys.argv[1], sys.argv[2])
