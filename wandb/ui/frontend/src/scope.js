import Webcam from "./plugins/Webcam";
import Upload from "./plugins/Upload";
import Audio from "./plugins/Audio";
import Draw from "./plugins/Draw";
import * as EG from "evergreen-ui";

export default {
  code: `<>
<strong>Hello World!</strong><br/>
<EG.Button onClick={() => callbacks.log("Clicked")}>Do something</EG.Button>
</>`,
  WB: { Webcam, Upload, Audio, Draw },
  EG: EG,
  callbacks: {
    log: stuff => console.log(stuff)
  }
};
