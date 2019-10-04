//binary indexed tree used to calculate sum of no starting from 0 to any index (prefix sum can also be used but in that update is 0(n) time but in binary index tree update is 0(logn) and getsum is also o(logn))
class BinaryIndextree// in this we can also use segment tree but it is complex to implement
{
	int bitree[];
	int arr[];
	BinaryIndextree(int arr[])
	{
		bitree=new int[arr.length+1];
		this.arr=arr;
		constructTree();

	}
	void constructTree()
	{
		int i=0;int j=0;
		while(i<arr.length)
		{
			j=i+1;

			while(j<arr.length+1)
			{
				bitree[j]+=arr[i];
				//System.out.println(j+" "+i);
				j=getnext(j);
			}
			i+=1;
		}
		// for(i=1;i<arr.length+1;i++)
		// {
		// 	System.out.print(bitree[i]+" ");
		// }
	}
	int getcomplement(int a)
	{
		int no_of_bits=(int)Math.floor(Math.log(a)/Math.log(2))+1;
		int comp_helper=(int)Math.pow(2,no_of_bits)-1;
		return (a^comp_helper)+1;
	}
	int getparent(int a)// in this we are just unsetting rightmost bit ex 8=1000 then parent =0000
	{
		return a-(a&getcomplement(a));
	}
	int getnext(int a) // in this we are getting next index
	{

		return a+(a&getcomplement(a));
	}
	int getsum(int d)
	{
		int j=d+1;
		int sum=0;
		while(j>0)
		{
			sum+=bitree[j];
			//System.out.println(j);
			j=getparent(j);
			
		}
		return sum;
	}
	void update(int i,int data)// updated i index ir arr[i] will now be data
	{
		int update_by_val=data-arr[i];
		int j=i+1;
		while(j<arr.length+1)// we are using same concept as constructing tree get val by how it is to be updated and then start from i+1 as bitree[0]=0 (node) and start update all next nodes
		{
			bitree[j]+=update_by_val;
			j=getnext(j);
		}
	}
	public static void main(String args[])
	{
		int arr[]={3,2,-1,6,5,4,-3,3,7,2,3};

		BinaryIndextree bin=new BinaryIndextree(arr);
		
		bin.update(2,1);
		System.out.println(bin.getsum(5));
	}
} 