// Full compact rank/split energy table, same lexicographic encoding and cost.
// Writes the caller's float64 buffer directly; never stores permutations.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <numeric>
#include <vector>
extern "C" std::uint64_t fill_cost(int n,const double* d,double* e,std::uint64_t size,double bound){
  if(n<1||n>15||!d||!e||bound<=0) return 0;
  std::fill(e,e+size,2.0);
  std::vector<int> a(n);std::iota(a.begin(),a.end(),1);
  std::vector<double> prefix(n);std::uint64_t pos=0;const int w=n+1;
  do{
    prefix[0]=0;
    for(int i=1;i<n;++i)prefix[i]=prefix[i-1]+d[a[i-1]*w+a[i]];
    double full=d[a[0]]+prefix[n-1]+d[a[n-1]*w];
    if(pos+std::uint64_t(n+1)>size)return 0;
    e[pos++]=full/bound;
    for(int k=1;k<n;++k){
      double value=d[a[0]]+prefix[k-1]+d[a[k-1]*w]+d[a[k]]+prefix[n-1]-prefix[k]+d[a[n-1]*w];
      e[pos++]=value/bound;
    }
    e[pos++]=full/bound;
  }while(std::next_permutation(a.begin(),a.end()));
  return pos;
}
