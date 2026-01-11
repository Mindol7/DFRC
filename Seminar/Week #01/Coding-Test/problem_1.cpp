#include <stdio.h>
#include <iostream>
using namespace std;

int main(){
    cout << "(1)" << endl; // 1번 피라미드
    // 코드 작성
    for(int i = 1; i <= 5; ++i){
        for(int j = 0; j < i; ++j){
            cout << "*";
        } cout << "\n";
    }
    cout << "\n" << endl;

    cout << "(2)" << endl; // 2번 피라미드
    // 코드 작성
    for(int i = 1; i <= 5; ++i){
        for(int j = 0; j < 2*i-1; ++j){
            cout << "*";
        } cout << "\n";
    }
    cout << "\n" << endl;

    cout << "(3)" << endl; // 3번 피라미드
    // 코드 작성
    for(int i = 5; i > 0; --i){
        for(int j = 0; j < i; ++j){
            cout << "*";
        } cout << "\n";
    }
    cout << "\n" << endl;

    
    cout << "(4)" << endl; // 4번 피라미드
    // 코드 작성
    for(int i = 5; i > 0; --i){
        for(int j = 1; j < i; ++j){
            cout << " ";
        }
        for(int j = 0; j <= 5-i; ++j){
            cout << "*";
        }
        cout << "\n";
    }
    cout << "\n" << endl;

    
    cout << "(5)" << endl; // 5번 피라미드
    // 코드 작성
    int k = 1;
    for(int i = 5; i > 0; --i){
        for(int j = 1; j < i; ++j){
            cout << " ";
        }
        for(int j = 0; j < 2*k-1; ++j){
            cout << "*";
        }
        for(int j = 1; j < i; ++j){
            cout << " ";
        }
        k++;
        cout << "\n";
    }
    cout << "\n" << endl;
    
    cout << "(6)" << endl; // 6번 피라미드
    k = 5;
    for(int i = 1; i <= 5; ++i){
        for(int j = 1; j < i; ++j){
            cout << " ";
        }
        for(int j = 0; j < 2*k-1; ++j){
            cout << "*";
        }
        for(int j = 1; j < i; ++j){
            cout << " ";
        }
        k--;
        cout << "\n";
    }
    cout << "\n" << endl;
}