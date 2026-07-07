"use client";
import React, {useEffect, useState} from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Phone, PhoneCall, Clock, TrendingUp, Users, CheckCircle, XCircle, History } from "lucide-react";
import Link from 'next/link';




type CallDetailsProps = {
  call_sid:string,
  duration:string,
  end_time:string,
  from:string,
  start_time:string,
  status:string,
  to:string

  
}
type RecentCallProps = {
  name: string,
  number: string,
  status: "completed" | "failed" | "busy" | "no-answer",
  duration: string,
  time: string
}

async function getData() {
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://virtual-telecaller.onrender.com';
  const res = await fetch(`${BACKEND_URL}/call_details`, {

    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Accpet": "application/json"
    }
  });
  if (!res.ok) {
    throw new Error("Failed to fetch data")
  }


  return res.json();
}

const DashboardPage = () => {

  const stats = [
    {title: "Total Calls Today", value: "47", icon: Phone, color: "text-blue-600"},
    {title: "Successful Calls", value: "32", icon: CheckCircle, color: "text-green-600"},
    {title: "Failed Calls", value: "15", icon: XCircle, color: "text-red-600"},
    {title: "Average Duration", value: "4:32", icon: Clock, color: "text-purple-600"},
  ]


  const [data,setData] = useState([]);
  const [recentData , setRecentData] = useState<RecentCallProps[]>([]);

  useEffect(() => {
    const fetchData = async ()=>{
      const data = await getData();

      // Filter first 4 calls for recent calls section
      const latestData = data.slice(0, 4).map((item: CallDetailsProps) => {
        const duration  = parseInt(item.duration);
        const formattedDuration = `${Math.floor(duration / 60)} :${(duration%60).toString().padStart(2,'0')}`;
        const endTime = new Date(item.end_time).getTime();
        
        const currentTime = new Date().getTime();
        const timeDifference = Math.floor((currentTime - endTime) / 60000); // difference in minutes

        let timeString = "";
        if (timeDifference < 1) {
          timeString = "Just now";
        } else if (timeDifference < 60) {
          timeString = `${timeDifference} min ago`;
        } 
        else if(timeDifference < 1440) {
          const hours = Math.floor(timeDifference / 60);
          if (hours === 1) {
            timeString = "1 hour ago";
          }
          else if (hours > 1) {

          timeString = `${hours} hours ago`;
          }
        }
        else if( timeDifference < 43200) {
          const days = Math.floor(timeDifference / 1440);
          timeString = `${days} day ago`;
        }
        else {
          const months = Math.floor(timeDifference / 43200);
          timeString = `${months} month ago`;
        }



        return{
          name: "From Telecaller",
          number: item.to,
          status: item.status,
          duration: formattedDuration,
          time: timeString,
        }

      })

      setRecentData(latestData);





      const today = new Date();

      // Filter data for today's calls

      const todayData = data.filter((item:CallDetailsProps)=>{
        const startTime = new Date(item.start_time);
        return startTime.getDate() ===today.getDate()&& startTime.getMonth()=== today.getMonth() &&startTime.getFullYear() === today.getFullYear();

      })

      setData(todayData);

    }

    fetchData();


    const interval = setInterval(fetchData, 10000); // run every 10 sec

    return () => clearInterval(interval);

  }, []);

  let totalCalls = 0;
  let successfulCalls = 0;
  let failedCalls = 0;
  let totalDuration =0;

  data.forEach((call:CallDetailsProps)=>{
    totalCalls+=1;
    if(call.status === "completed"){
      successfulCalls +=1;
      totalDuration += parseInt(call.duration);


    }
    else if (call.status === "failed"){
      failedCalls +=1;
    }
    
  })

  let averageDuration  = "0:00";
  if(successfulCalls>0){
    const minutes = Math.floor(totalDuration/60);
    const seconds = totalDuration % 60;
    averageDuration=  `${minutes}:${seconds.toString().padStart(2,'0')}`;
   


  }

  stats[0].value = totalCalls.toString();
  stats[1].value = successfulCalls.toString();
  stats[2].value = failedCalls.toString();
  stats[3].value = averageDuration;







  return (

    <div className='p-6 space-y-6 min-h-screen max-w-7xl mx-auto'>

      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold  text-gray-900 dark:text-white">Dashboard</h1>
        <Button className="flex items-center gap-2">
          <PhoneCall className="h-4 w-4" />
                 <Link href = "/makeCall">
              Make a new Call
              </Link>
        </Button>
      </div>


      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>

        {stats.map((stat,index)=>{

          const Icon = stat.icon;
          return (
            <Card key = {index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                  </div>
                  <Icon className={`h-8 w-8 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          )
        })}



      </div>



      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>

        {/* Recent Calls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Recent Calls
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentData.map((call, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white">{call.name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{call.number}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={call.status === "completed" ? "default" : "destructive"}>{call.status}</Badge>
                    <div className="text-right">
                      <p className="text-sm font-medium">{call.duration}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{call.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="w-full justify-start bg-transparent" variant="outline">
              <Phone className="h-4 w-4 mr-2" />
              <Link href = "/makeCall">
              Make Quick Call
              </Link>
            </Button>
            <Button className="w-full justify-start bg-transparent" variant="outline">
              <Users className="h-4 w-4 mr-2" />

              <Link href = "/callLogs">
              View Call History
              </Link>
            </Button>
            {/* <Button className="w-full justify-start bg-transparent" variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Calls
            </Button> */}
            <Button className="w-full justify-start bg-transparent" variant="outline">
              <TrendingUp className="h-4 w-4 mr-2" />
              <Link href = "/analytics">
              View Analytics
              </Link>
            </Button>
          </CardContent>
        </Card>


        </div>

    </div>
  )


}

export default DashboardPage;