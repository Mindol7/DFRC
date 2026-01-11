#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
using namespace std;

struct node{ // 이진 탐색 트리의 노드 구조체
    int key;
    struct node *left, *right;
};

struct node *makeNode(int data)
{
    struct node *ptr = (struct node *)malloc(sizeof(struct node));
    ptr -> key = data;
    ptr -> left = ptr -> right = NULL;
    return ptr;
} // 매개변수로 받은 data를 저장하는 노드 구조체를 만들어 반환하는 함수
// ptr 포인터는 node 크기만큼의 메모리를 동적으로 할당 받음
// key는 data, left와 right는 NULL로 초기화한 후 반환

struct node *insert(struct node *node, int data)
{
    // 이진 탐색 트리에 데이터를 하나 추가하는 재귀함수
    if(node == NULL){
        return makeNode(data);
    } 
    if(data < node->key) node->left = insert(node->left, data);
    else node->right = insert(node->right, data);

    return node;
} 


struct node *minNode(struct node *node)
{
    struct node *cur = node;
    // 가장 작은 노드 가져오기
    while(cur && cur->left){
        cur = cur->left;
    }
    return cur;
}

struct node* deleteNode(struct node* node, int data) // 이진탐색트리에서 data를 삭제하는 재귀함수
{
    if (node == NULL) // node가 NULL이라면 그대로 반환
        return node;
    if (data < node -> key) // 삭제할 data가 node -> key보다 작다면 왼쪽 자식 노드를 매개변수로 deleteNode 함수를 재귀호출
        node -> left = deleteNode(node -> left, data);
    else if (data > node -> key) // 삭제할 data가 node -> key보다 크면 오른쪽 자식 노드를 매개변수로 deleteNode 함수를 재귀호출
        node -> right = deleteNode(node -> right, data);
    else { // node가 삭제할 노드이며 노드의 삭제는 세 가지 경우가 존재
        // case (1), (2)
        if (node -> left == NULL)
        {
            // 코드 작성
            struct node *tmp = node->right;
            delete node;
            return tmp;
        }
        else if (node -> right == NULL)
        {
            // 코드 작성
            struct node* tmp = node->left;
            delete node;
            return tmp;
        }

        // case (3)
        struct node *tmp = minNode(node -> right);
        
        // 코드 작성
        node->key = tmp->key;
        node->right = deleteNode(node->right, tmp->key);
    }
    return node;
}

void inorder(struct node *node) // 이진 탐색 트리를 inorder 순회하는 재귀함수
{
    if(node == NULL){
        return;
    }
    inorder(node->left);
    cout << node->key << " -> ";
    inorder(node->right);
}

int main() // data[] 배열에 있는 값들을 insert
{
    struct node *root = NULL;
    int data[] = {10, 8, 6, 9, 7, 15, 12, 14}; // 입력 데이터
    int del; // 삭제 노드

    // 코드 작성

    // STEP 1: Insert Data
    for(int i = 0; i < 8; ++i){
        root = insert(root, data[i]);
    }
    inorder(root); // inorder 함수를 호출하여 트리 내용을 출력

    int key;
    while (1) // -1이 입력될 때까지 삭제할 노드를 입력받아 deleteNode를 수행하고 inorder로 출력
    {
        cout << "\n Enter node to delete(-1 to quit): ";

        // 코드 작성
        cin >> key;
        if(key == -1){
            return 1;
        }
        // 삭제
        root = deleteNode(root, key);
        // 순회
        inorder(root);
    }
}