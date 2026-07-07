
"use client"

import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Phone } from "lucide-react"


import React from "react"
import { useState } from "react"

interface CallSectionProps {
    businessName: string,
    businessInfo: string,
    systemPrompt: string,
    sourceNumber: string,
    destinationNumber: string,
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://virtual-telecaller.onrender.com';

export function CallSection() {





    const [formData, setFormData] = useState<CallSectionProps>({
        businessName: "",
        businessInfo: "",
        systemPrompt: "",
        sourceNumber: "",
        destinationNumber: "",
    })



    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target

        setFormData({
            ...formData,
            [name]: value
        })
    }








    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {

        e.preventDefault()
        console.log("formData", formData)

        try {
            
            const response = await fetch(`${BACKEND_URL}/information`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),


            });



            if (!response.ok) {
                throw new Error("Network response was not ok")
            }



            const data = await response.json()
            console.log("Response data:", data)

            







            setTimeout(async () => {

                try {

                    const callResponse = await fetch(`${BACKEND_URL}/make_call`, {
                        method: "GET",
                    });

                    const calld = await callResponse.text()
                    console.log("Call Response:", calld)



                     window.location.href = "/chat"  // Redirect to the chat page after 5 seconds





                }
                catch (error) {
                    console.error("Error:", error)
                }

            }, 5000)
        }

        catch (error) {
            console.error("Error:", error)
        }




    }
    return (
        <div className="bg-white dark:bg-[#1b1b1b]  mx-auto rounded-md shadow-md mt-6 w-full md:w-1/2 transition-colors duration-300 ease-in-out">

            <div className="flex flex-col items-center justify-center mb-8">
                <div className="flex items-center mb-4 gap-1 mt-4">
                    <Phone className="h-8 w-8 text-emerald-600" />
                    <h2 className="text-4xl font-bold  text-gray-800 dark:text-white">Call Section</h2>
                </div>

                <p className="text-emerald-600 text-xl font-bold text-center mb-10">
                    Enter your Details to get started
                </p>

                <form className="items-center justify-center w-66 md:w-3/4" onSubmit={handleSubmit}>

                    {/* Business Name */}
                    <div className="mb-4 w-full flex flex-col gap-1">
                        <label htmlFor="businessName" className="text-gray-700 dark:text-gray-300 font-bold mb-2">
                            Business Name
                        </label>
                        <Input
                            type="text"
                            id="businessName"
                            name="businessName"
                            placeholder="Enter your business name"
                            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100 rounded-md p-2"
                            required
                            onChange={handleChange}
                        />
                    </div>

                    {/* Business Info */}
                    <div className="mb-4 w-full flex flex-col gap-1">
                        <label htmlFor="businessInfo" className="text-gray-700 dark:text-gray-300 font-bold mb-2">
                            Business Information
                        </label>
                        <Textarea
                            id="businessInfo"
                            name="businessInfo"
                            placeholder="Enter your business information"
                            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100 rounded-md p-2 h-28"
                            required
                            onChange={handleChange}
                        />
                    </div>

                    {/* System Prompt */}
                    <div className="mb-4 w-full flex flex-col gap-1">
                        <label htmlFor="systemPrompt" className="text-gray-700 dark:text-gray-300 font-bold mb-2">
                            System Prompt
                        </label>
                        <Textarea
                            id="systemPrompt"
                            name="systemPrompt"
                            placeholder="Enter your system prompt"
                            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100 rounded-md p-2 h-28"
                            required
                            onChange={handleChange}
                        />
                    </div>

                    {/* Source Number */}
                    <div className="mb-4 w-full flex flex-col gap-1">
                        <label htmlFor="sourceNumber" className="text-gray-700 dark:text-gray-300 font-bold mb-2">
                            Source Number
                        </label>
                        <Input
                            type="text"
                            id="sourceNumber"
                            name="sourceNumber"
                            placeholder="Enter your source number"
                            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100 rounded-md p-2"
                            required
                            onChange={handleChange}
                        />
                    </div>

                    {/* Destination Number */}
                    <div className="mb-4 w-full flex flex-col gap-1">
                        <label htmlFor="destinationNumber" className="text-gray-700 dark:text-gray-300 font-bold mb-2">
                            Destination Number
                        </label>
                        <Input
                            type="text"
                            id="destinationNumber"
                            name="destinationNumber"
                            placeholder="Enter your destination number"
                            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100 rounded-md p-2"
                            required
                            onChange={handleChange}
                        />
                    </div>

                    {/* Submit Button */}
                    <div className="flex justify-center w-full">
                        <button
                           


                            type="submit"
                            className="bg-emerald-600 text-white font-bold py-4 px-6 rounded-lg hover:bg-emerald-700 w-36 transition-all duration-200 hover:cursor-pointer"
                        >
                            Initiate Calls
                        </button>


                        




                    </div>

                </form>
            </div>
        </div>



    )

}