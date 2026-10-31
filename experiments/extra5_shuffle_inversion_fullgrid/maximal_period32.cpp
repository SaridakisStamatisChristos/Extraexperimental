// Primitive-period filter for xorshift32 transitions, independently calculated.
// A linear map with a nonzero orbit of length 2^32-1 has a full 32-bit cycle.
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
using U32=uint32_t;using U64=uint64_t;
using Matrix=std::array<U32,32>;
inline U32 step(U32 x,int a,int b,int c,int direction){
 if(!direction){x^=x<<a;x^=x>>b;x^=x<<c;}
 else{x^=x>>a;x^=x<<b;x^=x>>c;}
 return x;
}
inline U32 apply(const Matrix&m,U32 v){U32 out=0;while(v){int b=std::countr_zero(v);out^=m[b];v&=v-1;}return out;}
inline Matrix square(const Matrix&m){Matrix out{};for(int i=0;i<32;i++)out[i]=apply(m,m[i]);return out;}
inline U32 power_orbit(const std::array<Matrix,32>&p,U64 exp){U32 v=1;int i=0;while(exp){if(exp&1)v=apply(p[i],v);exp>>=1;i++;}return v;}
int main(int argc,char**argv){
 if(argc<2){std::cerr<<"usage: maximal_period32 output.csv\n";return 2;}
 std::ofstream out(argv[1]);out<<"direction,a,b,c,maximal_period\n";
 constexpr U64 M=0xFFFFFFFFULL;
 constexpr std::array<U64,5> factors{3,5,17,257,65537};
 U64 total=0,primitive=0;
 for(int a=1;a<=31;a++)for(int b=1;b<=31;b++)for(int c=1;c<=31;c++)for(int d=0;d<2;d++){
   total++;
   std::array<Matrix,32> powers{};
   for(int i=0;i<32;i++)powers[0][i]=step(1U<<i,a,b,c,d);
   for(int i=1;i<32;i++)powers[i]=square(powers[i-1]);
   if(power_orbit(powers,M)!=1)continue;
   bool full=true;
   for(U64 f:factors)if(power_orbit(powers,M/f)==1){full=false;break;}
   if(full){primitive++;out<<d<<','<<a<<','<<b<<','<<c<<",1\n";}
 }
 std::cout<<"tested_transitions="<<total<<" maximal_period="<<primitive<<"\n";
}
