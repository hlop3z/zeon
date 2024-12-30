const PYTHON_CODE = `
import js
    
div = js.document.createElement("div")
div.innerHTML = "<h1>This element was created from Python</h1>"
js.document.body.prepend(div)
`;

async function main(py) {
  py.runPython("import sys");
  py.runPython(PYTHON_CODE);

  const py_version = py.globals.get("sys").version;
  console.log(py_version);
}
