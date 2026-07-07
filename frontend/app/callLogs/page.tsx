
"use client"


import React from 'react'

import { useState } from 'react'
import { useEffect } from 'react';
import { DataTable } from './datatable';
import { columns } from './columns';
import Link from 'next/link';


async function getData() {

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://virtual-telecaller.onrender.com';
  const res = await fetch(`${BACKEND_URL}/call_details`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    }

  });

  if (!res.ok) {
    throw new Error("Failed to fetch data")
  }

  return res.json()
}



export default function CallDetails() {


  // const data = await getData()

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true);



  useEffect(() => {


    const fetchData = async () => {
      try {
        const callData = await getData();
        setData(callData);
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData()
    const interval = setInterval(fetchData, 10000)

    return () => clearInterval(interval)


  }, [])






  console.log("Data", data)
  // console.log("Data", data)
  return (
    <div className="bg-gradient-to-b from-gray-50 to-gray-200 dark:from-[#0d0d0d] dark:to-[#1a1a1a] min-h-screen flex flex-col items-center justify-center">

      <div className="shadow-md rounded-md bg-white dark:bg-[#121212] text-black dark:text-gray-200 mx-auto p-10 w-full max-w-6xl">
        <h1 className="text-2xl font-bold text-center mb-4">Call Records</h1>
        <p className="text-center text-gray-600 dark:text-gray-400 mb-6">
          All your call records are displayed below.
        </p>

        {loading ? (
          <div className="text-center py-20 text-lg font-medium text-gray-500 dark:text-gray-400 animate-pulse">
            ⏳ Fetching data...
          </div>

        ) : (
          <>
            <DataTable columns={columns} data={data} />
            <div className="text-center mt-6">
              <Link href="/dashboard">
                <button className="bg-green-500 text-white dark:bg-green-600 px-4 py-2 rounded-md hover:bg-green-600 dark:hover:bg-green-700 transition-colors duration-300">
                  Go to Dashboard
                </button>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}