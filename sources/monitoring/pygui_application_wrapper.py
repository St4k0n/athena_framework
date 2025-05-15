from render.benchmark import render_benchmark

def get_application_base():
    return {
        "Benchmark": {
            "label": "Benchmark",
            "render": render_benchmark,
            "open": False,
        }
    }