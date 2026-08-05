class practise{
    public static void main(String[] args){
        int n = 5;
        System.out.println(fibonacci(5));
    }
    public static int fibonacci(int n){
        int result =0;
        if (n==1) result = 1;
        if(n==2) result =2;
        if(n==3) result =3;
        else{
            result = fibonacci(n-1)+fibonacci(n-2);
        }
        return result;
    }
}
