
// import mongoose from 'mongoose';
import mongoose , {Mongoose} from "mongoose";

const MONGODB_URI = process.env.MONGODB_URI as string;




if( !MONGODB_URI){
    throw new Error('Please define the MONGODB_URI environment variable inside .env.local');
}

const cached: { conn: Mongoose | null; promise: Promise<Mongoose> | null } = {
  conn: null,
  promise: null,
};


async function dbConnect(): Promise<Mongoose> {
  if (cached.conn) return cached.conn;

  if (!cached.promise) {
    cached.promise = mongoose.connect(MONGODB_URI).then((mongoose) => mongoose);
  }

  cached.conn = await cached.promise;
  return cached.conn;
}

export default dbConnect;
