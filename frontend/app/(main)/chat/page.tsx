"use client"
import Link from 'next/link';
import React from 'react'
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';





const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://virtual-telecaller.onrender.com';
const socket = io(BACKEND_URL);

const ChatPage = () => {

    type MessageProps = {
        label: string,
        text: string,
    }

    const [messages, setMessages] = useState<MessageProps[]>([]);

    useEffect(() => {
        socket.on("chat_message", (data) => {
            setMessages((prev) => [...prev, data]);
        });

        return () => { socket.disconnect(); }





    }, [])


    return (

        <div className='min-h-screen min-w-full '>
            <div className='flex flex-col items-center justify-start h-screen p-1'>

                <h1 className='text-4xl font-bold dark:text-white mb-2 text-gray-950'>Live Call Chat</h1>

                <div className='min-w-full max-w-xl '>

                    {/* Scrollable message box */}
                    <div className=' p-6 rounded-2xl h-[65vh] w-full overflow-y-auto 
                    '>
                        {messages.map((msg, index) => (
                            <div key={index} className='mb-7 p-6 rounded-lg bg-gray-200 dark:bg-gray-700 shadow-md hover:bg-white dark:hover:bg-gray-600 transition-colors duration-200'>
                                <strong className='bg-gray-400 dark:bg-gray-800 text-black dark:text-white font-bold p-2 rounded-md mr-3'>
                                    {msg.label}:
                                </strong>

                                <span className='text-gray-900 dark:text-gray-100 text-lg'>
                                    {msg.text}
                                </span>

                            </div>
                        ))}
                    </div>

                </div>

                <div className='flex items-center justify-center mt-4'>

                    <button
                        className='bg-green-500 text-white dark:bg-green-700 px-4 py-2 rounded-md shadow-md hover:bg-green-600 dark:hover:bg-green:800 transistion-colors duration-200'>

                        <Link href='/dashboard' className='text-white dark:text-white font-semibold'>
                            Go to Dashboard
                        </Link>
                    </button>


                </div>

            </div>

        </div>
    )
}

export default ChatPage