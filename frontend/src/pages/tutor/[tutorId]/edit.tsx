import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form"
import { UseFormReturn, useForm } from "react-hook-form"
import * as z from "zod"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { useState } from "react"
import LoadingButton from "@/components/loadingButton"
import { HTTPAuthService } from "@/service/authService"
import { getErrorMessage } from "@/lib/utils"
import toast from "react-hot-toast"
import { ThemeToggle } from "@/components/themeToggle"
import { Toaster } from "react-hot-toast"
import { zodResolver } from "@hookform/resolvers/zod"
import useUser from "@/hooks/useUser"
import { useRouter } from "next/router"

const authService = new HTTPAuthService()

const formSchema = z.object({
  name: z
    .string()
    .min(1, {
      message: "Name is too short",
    })
    .max(50),
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
  const { user } = useUser()
  //  const id = user?.userId
  const router = useRouter()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  })
  const [submitLoading, setSubmitLoading] = useState(false)
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    //need to modify to convert from image to base64URI values.profilePicture
    setSubmitLoading(true)
    try {
      //will need to create a mock implementation of the edit api/return values
      //const id = await userService.edit(values)
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
      <div className="pt-10">
        <Button asChild>
          <a href={`../${user?.userId}`}> Return to profile </a>
        </Button>
      </div>
      <div className="grid w-full place-content-center">
        <Card className="w-screen max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Edit Profile </CardTitle>
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
                  <CustomFormField form={form} name="name" label="Name" />
                  <FormField
                    control={form.control}
                    name="name"
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
                  name="bio"
                  form={form}
                  inputType="string"
                  label="Bio"
                />
                <CustomFormField
                  name="email"
                  form={form}
                  label="Email"
                  inputType="email"
                />
                <CustomFormField
                  name="profilePicture"
                  form={form}
                  label="Profile Picture"
                  inputType="file"
                />
                <CustomFormField
                  name="location"
                  form={form}
                  label="Location"
                  inputType="string"
                />
                <CustomFormField
                  name="phoneNumber"
                  form={form}
                  label="Phone Number"
                  inputType="string"
                />
                <CustomFormField
                  name="courseOfferings"
                  form={form}
                  label="Course Offerings"
                  inputType="string"
                />
                {/* come back to check on this -> need multiple inputs*/}
                <CustomFormField
                  name="timeAvailable"
                  form={form}
                  label="Available Times"
                  inputType="String"
                />

                <div className="mt-4">
                  <LoadingButton
                    role="submit"
                    className="w-full"
                    isLoading={submitLoading}
                  >
                    Edit
                  </LoadingButton>
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
    formDescription?: string
  }

  function CustomFormField({
    label,
    form,
    name,
    inputType,
    formDescription,
  }: CustomFormFieldProps) {
    return formDescription ? (
      <FormField
        control={form.control}
        name={name}
        render={({ field }) => (
          <FormItem>
            <Label>{label}</Label>
            <FormControl>
              <Input {...field} type={inputType} />
            </FormControl>
            <FormDescription>{formDescription}</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    ) : (
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
