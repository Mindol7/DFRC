#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <iostream>

using namespace std;

int passwordChecker(char password[]);

int main(int argc, char* argv[]) // 
{
	char password[30];
	char password_buf[256];
	// strncpy(password_buf, argv[1], sizeof(password_buf)); // 필요없는 명령이므로 삭제
    
	printf("패스워드 입력(8글자 이상, 대소문자/숫자/특수문자 포함):");
    scanf("%s", password_buf);
    // scanf("%s", password); // Buffer Overflow 발생 위험
    snprintf(password, 30, password_buf);
	// printf(password_buf); // format-string-bug 발생가능하므로 수정하지만 필요없으므로 삭제
    
    cout << "\n입력된 패스워드 : " << password << endl;
    int r = passwordChecker(password);
    return r;
}

int passwordChecker(char password[])
{
	// double passwordCheck = 0;
    int passwordCheck = 0;
	int checkUpper = 0;
	// int checkLower = 0; // checkLower가 2번 선언되므로 한개 삭제
	int checkLower = passwordCheck; // type confusion 발생 가능하므로 passwordCheck을 int로 변경한다.
	int* checkDigit = NULL; // Null Pointer Dereference 취약점 발생 가능하므로 사용 후 free 할 것
	int* checkSpecial = 0;
    int true_val = 1; 
	// free(checkSpecial); // 뒤에서 checkSpecial을 사용하므로 free를 뒤에 배치

	if (strlen(password) < 8){
        cout << "8글자 이상이어야 합니다." << endl;
        return 1;
    }
		
	// free(checkSpecial); // double free 취약점 발생 가능하므로 free를 한개만 작성하도록 한다.

	for (int i = 0; i < strlen(password); i++) {
		if (isupper(password[i]))
			checkUpper = 1;
		else if (islower(password[i]))
			checkLower = 1;
		else if (isdigit(password[i])){
            // checkDigit = 1; // Type Confusion
			checkDigit = (int*)1;
        }
		else
            // checkSpecial = 1; // Type Confusion
			checkSpecial = (int*)1;
	}

	if (checkUpper == 0) {
        cout << "영문 대문자가 하나 이상이어야 합니다." << endl;
        return 2;
    }
	if (checkLower == 0) {
        cout << "영문 소문자가 하나 이상이어야 합니다." << endl;
        return 3;
    }
	if (checkDigit == 0) {
        cout << "숫자가 하나 이상이어야합니다." << endl;
        return 4;
    }
	if (checkSpecial == 0) {
        cout << "특수문자가 하나 이상이어야 합니다." << endl;
        return 5;
    }
    checkDigit = NULL; // checkDigit과 checkSpecial에 Use-After-Free 가능하므로 NULL 할당해줌
    checkSpecial = NULL;
    free(checkDigit);
    free(checkSpecial);    
    cout << "규칙에 맞는 패스워드 입니다." << endl;

    return 0;
}