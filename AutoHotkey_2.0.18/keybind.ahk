
XButton1::
{
    ; Use FormatTime to get the current date in MM/dd/yyyy format
    currentDate := FormatTime(A_Now, "MM/dd/yyyy")
    ; Add a space after the formatted date
    formattedDateWithSpace := currentDate " "
    ; Send formatted input
    SendInput(formattedDateWithSpace)
    return
}
