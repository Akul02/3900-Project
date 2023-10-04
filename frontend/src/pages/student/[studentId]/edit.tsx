import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form"
import { UseFormReturn, useForm } from "react-hook-form"
import * as z from "zod"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import Link from "next/link"
import { Label } from "@/components/ui/label"
import { useState } from "react"
import LoadingButton from "@/components/loadingButton"
import { HTTPAuthService } from "@/service/authService"
import { getErrorMessage } from "@/lib/utils"
import toast from "react-hot-toast"
import { ThemeToggle } from "@/components/themeToggle"
import { Toaster } from "react-hot-toast"
import { zodResolver } from "@hookform/resolvers/zod"

const authService = new HTTPAuthService()

const formSchema = z.object({
  string: z.string(),
  name: z.string(),
  bio: z.string(),
  email: z.string(),
  profilePicture: z.string().optional(),
  location: z.string().optional(),
  phoneNumber: z.string().optional(),
  courseOfferings: z.string().array(),
  timeAvailable: z
    .object({
      startTime: z.string(),
      endTime: z.string(),
    })
    .array(),
})

export default function Edit() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  })
  const [submitLoading, setSubmitLoading] = useState(false)
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setSubmitLoading(true)
    try {
      const id = await authService.register(values)
    } catch (error) {
      toast.error(getErrorMessage(error))
    }
    setSubmitLoading(false)
  }

  //need to create form with zod to hold the information
  return (
    <div className="flex h-screen w-screen">
      <Toaster />
      <ThemeToggle />
      <div className="grid w-full place-content-center">
        <Card className="w-screen max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Edit Profile</CardTitle>
            <CardDescription>Change your details here!</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form
                className="flex flex-col gap-4"
                onSubmit={form.handleSubmit(onSubmit)}
                noValidate
              >
                <div className="grid grid-cols-2 items-end gap-4">
                  <CustomFormField form={form} name="name" label="Full Name" />
                  <FormField
                    control={form.control}
                    name="accountType"
                    render={({ field }) => (
                      <FormItem>
                        <FormControl>
                          <Select onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select Account Type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="student">Student</SelectItem>
                              <SelectItem value="tutor">Tutor</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage>
                          {/* We need this so the select box is 
                      aligned when name has an error */}
                          {form.getFieldState("name").invalid && "\xa0"}
                        </FormMessage>
                      </FormItem>
                    )}
                  />
                </div>
                <CustomFormField
                  name="email"
                  form={form}
                  inputType="email"
                  label="Email"
                />
                <CustomFormField
                  name="password"
                  form={form}
                  label="Password"
                  inputType="password"
                />
                <div className="mt-4">
                  <LoadingButton
                    role="submit"
                    className="w-full"
                    isLoading={submitLoading}
                  >
                    Submit
                  </LoadingButton>
                  <Button asChild variant="link" className="px-0">
                    <Link href={"/login"}>Login instead</Link>
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  interface CustomFormFieldProps {
    form: UseFormReturn<z.infer<typeof formSchema>, any, undefined>
    name: keyof z.infer<typeof formSchema>
    label: string
    inputType?: string
  }

  function CustomFormField({
    label,
    form,
    name,
    inputType,
  }: CustomFormFieldProps) {
    return (
      <FormField
        control={form.control}
        name={name}
        render={({ field }) => (
          <FormItem>
            <Label>{label}</Label>
            <FormControl>
              <Input {...field} type={inputType} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    )
  }
}
