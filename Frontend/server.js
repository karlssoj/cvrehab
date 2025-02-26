import express from "express";
import { Server } from "socket.io";
import { createServer } from "node:http";

const app = express();
const port = 3000;

// Create server with node
const server = createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// Host a static website with express
app.use(express.static("public"));

io.on("connection", (socket) => {
  console.log("A user connected");

  socket.on("disconnect", () => {
    console.log("User disconnected");
  });
});

// Starts application
server.listen(port, () => {
  console.log(`server running at http://localhost:${port}`);
});
