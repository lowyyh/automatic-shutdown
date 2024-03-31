#include <windows.h>  
#include <stdio.h>  
  
int IsDarkModeEnabled() {  
    DWORD appsUseLightTheme = 1; // 假设为浅色模式  
    DWORD type = REG_DWORD;  
    HKEY hKey;  
    LONG result = RegOpenKeyExA(HKEY_CURRENT_USER,  
        "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",  
        0, KEY_READ, &hKey);  
    if (result == ERROR_SUCCESS) {  
        DWORD size = sizeof(appsUseLightTheme);  
        result = RegQueryValueExA(hKey, "AppsUseLightTheme", NULL, &type,  
            (LPBYTE)&appsUseLightTheme, &size);  
        RegCloseKey(hKey);  
    }  
    // 如果AppsUseLightTheme为0，则为深色模式；否则为浅色模式  
    return appsUseLightTheme == 0;  
}  