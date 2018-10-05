library(pbdZMQ, quietly = TRUE)

recv_multipart <- function(socket){
  ret <- list()
  i.part <- 1
  r <- zmq.recv(socket, flags = .pbd_env$ZMQ.SR$BLOCK)
  ret[[i.part]] <- r$buf
  opt.val <- zmq.getsockopt(socket, .pbd_env$ZMQ.SO$RCVMORE, 0L)

  while(opt.val == 1){
    i.part <- i.part + 1
    r <- zmq.recv(socket, flags = .pbd_env$ZMQ.SR$BLOCK)
    ret[[i.part]] <- r$buf
    opt.val <- zmq.getsockopt(socket, .pbd_env$ZMQ.SO$RCVMORE, 0L)
  }

  list(buf=ret, len=i.part)
}

context <- zmq.ctx.new()
subscriber <- zmq.socket(context, .pbd_env$ZMQ.ST$SUB)
zmq.connect(subscriber, "tcp://127.0.0.1:12345")
zmq.setsockopt(subscriber, .pbd_env$ZMQ.SO$SUBSCRIBE, "")
Sys.sleep(0.5)

for(i in 1:5){
  ret <- recv_multipart(subscriber)
  if(ret$len != -1){
    cat("Message:", paste(ret$buf), "\n")
  } else{
    break
  }
}

zmq.close(subscriber)
zmq.ctx.destroy(context)
