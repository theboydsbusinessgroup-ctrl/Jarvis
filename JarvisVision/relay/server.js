import express from "express";

const app = express();
app.use(express.raw({type:"image/jpeg", limit:"5mb"}));
let latest = null;
const token = process.env.JARVIS_VISION_TOKEN;

function auth(req,res,next){
  if (!token || req.headers.authorization !== `Bearer ${token}`) return res.sendStatus(401);
  next();
}
app.post("/api/frame", auth, (req,res) => {
  latest = {data: Buffer.from(req.body), at: new Date().toISOString()};
  res.sendStatus(204);
});
app.get("/api/frame/latest", auth, (req,res) => {
  if (!latest) return res.sendStatus(404);
  res.set("X-Jarvis-Captured-At", latest.at).type("jpeg").send(latest.data);
});
app.get("/health", (_,res)=>res.json({ok:true, frame:!!latest}));
app.listen(process.env.PORT || 3000);
