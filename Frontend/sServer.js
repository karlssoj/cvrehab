import express from "express";
import { Server as SocketIOServer } from "socket.io";
import { readFileSync } from "node:fs";
import { createServer } from "node:https";

const app = express();
const port = 3333;

// Load SSL certificate and private key
const options = {
  key: readFileSync('/home/jenna/key.pem'),
  cert: readFileSync('/home/jenna/cvrehab.pem'),
  passphrase: 'test'
};

// Create HTTPS server with node
const server = createServer(options, app);
const io = new SocketIOServer(server, { cors: { origin: "*" } });

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
  console.log(`server running at https://localhost:${port}`);
});
