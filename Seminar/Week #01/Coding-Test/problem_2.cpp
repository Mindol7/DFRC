#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <iostream>
#define MAX 30
using namespace std;

void swap(int v[], int i, int j)
{   // i: prev, j: post
    int tmp = v[i];
    v[i] = v[j];
    v[j] = tmp;
}

int partition(int v[], int p, int r){
        int x = v[r];
        int i = p-1;
        for(int j = p; j < r; ++j){
            if(v[j] < x){
                i = i + 1;
                swap(v[i], v[j]);
            }
        }
        swap(v[i+1], v[r]);
        return i+1;
    }

void sort(int v[], int left, int right) // Quick Sort
{
    if (left < right){
            int q = partition(v, left, right);
            sort(v, left, q-1);
            sort(v, q+1, right);
        }
}

int main()
{
    int data_1[MAX] = {
        15638, 20998, 7424, 18785, 23617, 23497, 29734, 26594, 4392, 5911,
        4725, 394, 13994, 24160, 26475, 2935, 25280, 20427, 14436, 5659,
        608, 2437, 15272, 3125, 27809, 89, 25768, 24063, 12575, 9346
    };

    int data_2[MAX] = {
        15540, 26226, 28555, 17781, 9092, 3999, 1896, 16108, 564, 25613,
        9163, 31841, 5188, 19290, 16070, 7080, 7172, 24726, 25051, 20815,
        18591, 29529, 23579, 22063, 15703, 28774, 9104, 21313, 7698, 20386
    };

    int data_3[MAX] = {
        15474, 7866, 31720, 28035, 32176, 23769, 5183, 9117, 30781, 18402,
        12121, 30960, 21162, 16044, 30978, 20766, 27868, 16670, 21204, 9073,
        19657, 14823, 18195, 12843, 18556, 4206, 8917, 19479, 4447, 5900
    };

    int v[MAX];
    // 첫 번째 데이터셋 정렬
    // 코드 작성
    for(int i = 0; i < MAX; ++i){
        v[i] = data_1[i];
    }
    cout << "\n \n";

    cout << "========Check Data_1 (Before/After Sorting) ========\n";
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";
    cout << "\n sorting\n" << endl;
    sort(v, 0, MAX-1);
    // 코드 작성
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";

    // 두 번째 데이터셋 정렬
    for(int i = 0; i < MAX; ++i){
        v[i] = data_2[i];
    }
    cout << "\n \n";

    cout << "========Check Data_2 (Before/After Sorting) ========\n";
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";
    cout << "\n sorting\n" << endl;
    sort(v, 0, MAX-1);
    // 코드 작성
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";

    // 세 번째 데이터셋 정렬
    for(int i = 0; i < MAX; ++i){
        v[i] = data_3[i];
    }
    cout << "\n \n";

    cout << "========Check Data_3 (Before/After Sorting) ========\n";
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";
    cout << "\n sorting\n" << endl;
    sort(v, 0, MAX-1);
    // 코드 작성
    for(int i = 0; i < MAX; ++i){
        if(i == 10 || i == 20 || i == 30){
            cout << "\n";
        }
        cout << v[i] << " ";
    }
    cout << "\n";

    return 0;
}