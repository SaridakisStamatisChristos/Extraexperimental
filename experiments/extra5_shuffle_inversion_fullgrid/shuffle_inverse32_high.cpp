// Exact shuffle-invariant inverse of xorshift32 with five successive
// modulo-without-replacement draws and a fixed number of extra state steps.
// Recovers state from the fourth selection, whose modulus is exactly 32.
// No dependency on public order of the five numbers.
// Multiply-high sampler: index = floor(x * size / 2^32), not modulo.
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <vector>
#include <unordered_set>
using U32=uint32_t;using U64=uint64_t;
struct Draw{U64 ticket;U32 allowed;};
struct Row{U32 coeff;U64 expr;};
struct Model{int a,b,c,dir,gap;};
static inline U32 step(U32 x,const Model &m){
 if(!m.dir){x^=x<<m.a;x^=x>>m.b;x^=x<<m.c;}
 else{x^=x>>m.a;x^=x<<m.b;x^=x>>m.c;}
 return x;
}
static U64 generate_ticket(U32&state,const Model&m){
 U64 remaining=(1ULL<<35)-1, ticket=0;
 for(int z=0;z<5;z++){
  state=step(state,m);
  unsigned n=35-z, j=(unsigned)(((U64)state*n)>>32);
  U64 avail=remaining;
  for(unsigned k=0;k<j;k++)avail&=avail-1;
  unsigned position=std::countr_zero(avail);
  U64 bit=1ULL<<position;
  ticket|=bit;remaining^=bit;
 }
 for(int j=0;j<m.gap;j++)state=step(state,m);
 return ticket;
}
static int match_prefix(U32 seed,const Model&m,const std::vector<Draw>&draws,int limit){
 int matched=0;
 for(int i=0;i<limit;i++){
  if(generate_ticket(seed,m)!=draws[i].ticket)break;
  matched++;
 }
 return matched;
}
static int rank_matrix(const std::array<U32,35>&rows){
 U32 piv[32]{};int rank=0;
 for(U32 x:rows){
  while(x){int p=31-std::countl_zero(x);if(!piv[p]){piv[p]=x;rank++;break;}x^=piv[p];}
 }
 return rank;
}
struct Inversion{
 // For each of 7 chosen 5-bit fourth indices, contributions to seed and syndrome.
 std::array<std::array<U32,32>,7> seed{};
 std::array<std::array<U32,32>,7> syndrome{};
 U32 dependent_count=0;
 std::vector<U32> null_basis;
 bool build(const std::array<U32,35>&rows){
  std::array<Row,32> pivot{};
  std::array<bool,32> found{};
  std::vector<U64> dependencies;
  for(int i=0;i<35;i++){
   U32 x=rows[i];U64 e=1ULL<<i;
   while(x){int p=31-std::countl_zero(x);
    if(!found[p]){pivot[p]={x,e};found[p]=true;break;}
    x^=pivot[p].coeff;e^=pivot[p].expr;
   }
   if(!x)dependencies.push_back(e);
  }
  null_basis.clear();
  std::vector<int> free_positions;
  for(int p=0;p<32;p++)if(!found[p])free_positions.push_back(p);
  if(free_positions.size()>4)return false;
  for(int f:free_positions){
    U32 state=1U<<f;
    for(int p=f+1;p<32;p++)if(found[p] && (std::popcount(pivot[p].coeff&state)&1))state|=1U<<p;
    null_basis.push_back(state);
  }
  dependent_count=dependencies.size();
  if(dependent_count>31)return false;
  std::array<U32,35> seed_delta{},syn_delta{};
  for(int i=0;i<35;i++){
   U64 rhs=1ULL<<i;
   U32 state=0;
   for(int p=0;p<32;p++){
    if(!found[p])continue;
    int y=(std::popcount(pivot[p].expr&rhs) ^ std::popcount(pivot[p].coeff&state))&1;
    if(y)state|=1U<<p;
   }
   seed_delta[i]=state;
   U32 syndrome=0;
   for(size_t j=0;j<dependencies.size();j++)if(std::popcount(dependencies[j]&rhs)&1)syndrome|=1U<<j;
   syn_delta[i]=syndrome;
  }
  for(int d=0;d<7;d++)for(int v=0;v<32;v++)for(int k=0;k<5;k++)if((v>>k)&1){
   seed[d][v]^=seed_delta[d*5+k];
   syndrome[d][v]^=syn_delta[d*5+k];
  }
  return true;
 }
};
struct Solver{
 const std::vector<Draw> &draws;
 int max_checked=0;
 U64 candidate_combinations=0, consistent=0, filter_survivors=0, one_ticket=0, two_tickets=0, max_prefix=0;
 U32 witness_seed=0;
 int matrix_rank=0, maximum_nullity=1;
 std::array<int,7> chosen{};
 std::array<std::vector<int>,7> values;
 std::array<std::array<U32,5>,4> extra_forms{};
 std::array<U32,4> extra_mask{};
 Inversion inv;
 Model model;
 explicit Solver(const std::vector<Draw>&x):draws(x){}
 // Enumerate only rank-consistent fourth indices, then check complete sets.
 void dfs(int depth,U32 state,U32 syn){
  if(depth==7){
   candidate_combinations++;
   if(syn)return;
   consistent++;
   const U32 variants=1U<<inv.null_basis.size();
   for(U32 mask=0;mask<variants;mask++){
     U32 candidate=state;
     for(size_t k=0;k<inv.null_basis.size();k++)if((mask>>k)&1U)candidate^=inv.null_basis[k];
     check_candidate(candidate);
   }
   return;
  }
  for(int v:values[depth])dfs(depth+1,state^inv.seed[depth][v],syn^inv.syndrome[depth][v]);
 }
 void check_candidate(U32 state){
   // Four additional necessary constraints derived from unknown-shuffle sets.
   // This preserves completeness but avoids costly five-output sampling.
   for(int j=0;j<4;j++){
     U32 fourth=0;
     for(int k=0;k<5;k++)fourth|=(U32)(std::popcount(extra_forms[j][k]&state)&1)<<k;
     if(!((extra_mask[j]>>fourth)&1U))return;
   }
   filter_survivors++;
   int prefix=match_prefix(state,model,draws,max_checked);
   if(prefix>=1)one_ticket++;
   if(prefix>=2)two_tickets++;
   if((U64)prefix>max_prefix){max_prefix=prefix;witness_seed=state;}
 }
 bool run(const Model&m,int selection_window,int prefix_limit){
  model=m;
  for(auto &v:values)v.clear();
  inv=Inversion{};
  max_checked=std::min((int)draws.size(),prefix_limit);
  candidate_combinations=consistent=filter_survivors=one_ticket=two_tickets=max_prefix=0;witness_seed=0;matrix_rank=0;
  // Candidate observations: smallest permitted fourth index sets in an early prefix.
  std::vector<int> ids(std::min((int)draws.size(),selection_window));std::iota(ids.begin(),ids.end(),0);
  std::sort(ids.begin(),ids.end(),[&](int a,int b){int ca=std::popcount(draws[a].allowed),cb=std::popcount(draws[b].allowed);return ca==cb?a<b:ca<cb;});
  // Precompute 5 output-bit linear forms for each ticket observation index.
  std::vector<std::array<U32,5>> forms(ids.size());
  std::vector<int> index_to_form(ids.size(),-1);
  for(int i=0;i<(int)ids.size();i++)index_to_form[ids[i]]=i;
  for(int bit=0;bit<32;bit++){
   U32 s=1U<<bit;
   for(int d=0;d<(int)ids.size();d++){
    U32 fourth=0;
    for(int z=0;z<5;z++){s=step(s,m);if(z==3)fourth=s;}
    for(int g=0;g<m.gap;g++)s=step(s,m);
    int fi=index_to_form[d];if(fi<0)continue;
    for(int k=0;k<5;k++)if((fourth>>(27+k))&1)forms[fi][k]|=1U<<bit;
   }
  }
  // Choose cheap observation sets, requiring exactly rank 32 for 35 equations.
  // Greedy minimize product of choice counts while expanding rank.
  std::vector<int> selected;
  std::vector<char> used(ids.size());
  int current_rank=0;
  for(int j=0;j<7;j++){
   int best=-1,best_rank=-1,best_count=100;
   for(int c=0;c<(int)ids.size();c++)if(!used[c]){
    std::array<U32,35> rr{};
    for(int q=0;q<(int)selected.size();q++)for(int k=0;k<5;k++)rr[q*5+k]=forms[selected[q]][k];
    for(int k=0;k<5;k++)rr[j*5+k]=forms[c][k];
    int rank=rank_matrix(rr);
    int count=std::popcount(draws[ids[c]].allowed);
    // Prefer rank progress; tie-break by least branching.
    if(rank>best_rank||(rank==best_rank&&count<best_count)){
     best=c;best_rank=rank;best_count=count;
    }
   }
   if(best<0)break;
   used[best]=1;selected.push_back(best);current_rank=best_rank;
  }
  matrix_rank=current_rank;
  if((int)selected.size()!=7||current_rank<32-maximum_nullity)return false;
  std::array<U32,35> rows{};
  for(int j=0;j<7;j++){
   chosen[j]=ids[selected[j]];
   for(int k=0;k<5;k++)rows[j*5+k]=forms[selected[j]][k];
   for(int v=0;v<32;v++)if((draws[chosen[j]].allowed>>v)&1U)values[j].push_back(v);
  }
  if(!inv.build(rows))return false;
  // The cheapest four unselected observations independently filter state candidates.
  int j=0;
  for(int c=0;c<(int)ids.size() && j<4;c++)if(!used[c]){
    extra_forms[j]=forms[c];extra_mask[j]=draws[ids[c]].allowed;j++;
  }
  if(j!=4)return false;
  dfs(0,0,0);
  return true;
 }
};
int main(int argc,char**argv){
 if(argc<3){std::cerr<<"usage: shuffle_inverse32 input.csv output.csv [triples=100] [gapmax=3] [window=100] [prefix=60] [offset=0] [maxfree=1]\n";return 2;}
 std::ifstream in(argv[1]);std::string line;std::getline(in,line);
 std::vector<Draw> draws;
 while(std::getline(in,line)){
  if(line.empty())continue;
  size_t p=line.find(','),q=line.find(',',p+1);if(p==std::string::npos||q==std::string::npos)return 3;
  Draw d{std::stoull(line.substr(p+1,q-p-1)),(U32)std::stoul(line.substr(q+1))};
  if(std::popcount(d.ticket)!=5||!d.allowed){std::cerr<<"bad input draw "<<draws.size()<<"\n";return 4;}
  draws.push_back(d);
 }
 int triples=argc>3?std::atoi(argv[3]):100;
 int gapmax=argc>4?std::atoi(argv[4]):3;
 int window=argc>5?std::atoi(argv[5]):100;
 int prefix=argc>6?std::atoi(argv[6]):60;
 int offset=argc>7?std::atoi(argv[7]):0;
 int maxfree=argc>8?std::atoi(argv[8]):1;
 std::unordered_set<U64> filter;
 if(argc>9){
   std::ifstream fin(argv[9]);
   if(!fin){std::cerr<<"filter file not readable\n";return 5;}
   std::string line;std::getline(fin,line);
   while(std::getline(fin,line)){
      int d,a,b,c,g;
      if(std::sscanf(line.c_str(),"%d,%d,%d,%d,%d",&d,&a,&b,&c,&g)!=5){std::cerr<<"invalid filter record\n";return 5;}
      filter.insert(((((U64)a*32+b)*32+c)*2+d)*16+g);
   }
 }

 if(maxfree<0||maxfree>4){std::cerr<<"maxfree must be 0..4\n";return 4;}
 std::ofstream out(argv[2]);
 out<<"direction,shift_a,shift_b,shift_c,extra_gap,enumerated,matrix_rank,selection_indices,branches,linear_consistent_seeds,passed_additional_fourth_constraints,one_exact,at_least_two_exact,max_exact_prefix,witness_seed\n";
 Solver solver(draws);solver.maximum_nullity=maxfree;auto start=std::chrono::steady_clock::now();
 U64 n=0,identified=0,total_branches=0,consistent=0,passed=0,max_prefix=0;
 int current=0;
 for(int a=1;a<=31;a++)for(int b=1;b<=31;b++)for(int c=1;c<=31;c++){
  if(current++<offset)continue;
  if(current>offset+triples)goto done;
  for(int dir=0;dir<2;dir++)for(int gap=0;gap<=gapmax;gap++){
   if(!filter.empty() && !filter.count(((((U64)a*32+b)*32+c)*2+dir)*16+gap))continue;
   Model m{a,b,c,dir,gap};bool found=solver.run(m,window,prefix);
   n++;identified+=found;
   total_branches+=solver.candidate_combinations;consistent+=solver.consistent;passed+=solver.filter_survivors;
   max_prefix=std::max(max_prefix,solver.max_prefix);
   out<<dir<<','<<a<<','<<b<<','<<c<<','<<gap<<','<<found<<','<<solver.matrix_rank<<",\"";
   if(found)for(int j=0;j<7;j++){if(j)out<<' ';out<<solver.chosen[j];}
   out<<"\","<<solver.candidate_combinations<<','<<solver.consistent<<','<<solver.filter_survivors<<','<<solver.one_ticket<<','<<solver.two_tickets<<','<<solver.max_prefix<<','<<solver.witness_seed<<'\n';
  }
 }
 done:
 out.close();
 const double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 std::cout<<"configs="<<n<<" rank32="<<identified<<" branches="<<total_branches<<" consistent="<<consistent<<" additional_pass="<<passed<<" maxprefix="<<max_prefix<<" seconds="<<sec<<"\n";
}
