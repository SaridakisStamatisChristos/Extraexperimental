// EXTRA 5: exact shuffle-invariant xorshift64 inverse engine.
// Pinned hypothesis: xorshift64(13,7,17), modulo-remaining-list sampler,
// five words per draw, persistent state, fixed inter-ticket gap.
// Input: CSV with ticket_mask column; zero masks represent missing observations.
// Output JSON; only fully enumerated branches may report UNSAT.
#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
using U64=uint64_t;
using U128=unsigned __int128;
using Five=std::array<U64,5>;
struct Draw {U64 mask;uint32_t allowed;};
constexpr U64 FULL=(1ULL<<35)-1;
struct Model {int a=13,b=7,c=17,dir=0,high=0;};
static Model model;
static inline U64 step(U64 s){
  if(!model.dir){s^=s<<model.a;s^=s>>model.b;s^=s<<model.c;}
  else{s^=s>>model.a;s^=s<<model.b;s^=s>>model.c;}
  return s;
}
static uint32_t allowed_mask(U64 mask){
  std::array<int,5> nums{};int n=0;
  for(int i=0;i<35;i++)if((mask>>i)&1ULL){if(n<5)nums[n]=i+1;n++;}
  if(n!=5)throw std::runtime_error("bad ticket bitmask");
  uint32_t a=0;
  for(int below=0;below<5;below++)
    for(int removed=std::max(0,below-1);removed<=std::min(3,below);removed++){
      int idx=nums[below]-1-removed;
      if(idx<0||idx>=32)throw std::runtime_error("invalid fourth index");
      a|=1u<<idx;
    }
  return a;
}
static U64 draw_ticket(U64 &state,int gap){
  U64 remaining=FULL,chosen=0;
  for(int i=0;i<5;i++){
    state=step(state);
    unsigned r=model.high?unsigned(((U128)state*(35-i))>>64):unsigned(state%(35-i));
    U64 avail=remaining;
    for(unsigned j=0;j<r;j++)avail&=avail-1;
    U64 bit=1ULL<<std::countr_zero(avail);
    remaining^=bit;chosen|=bit;
  }
  for(int i=0;i<gap;i++)state=step(state);
  return chosen;
}
static std::vector<Draw> read_csv(const std::string &file){
  std::ifstream in(file);
  if(!in)throw std::runtime_error("cannot open input");
  std::string hdr;std::getline(in,hdr);
  size_t col=0,pos=0;bool found=false;
  while(true){
    size_t end=hdr.find(',',pos);
    std::string f=hdr.substr(pos,end==std::string::npos?end:end-pos);
    if(!f.empty()&&f.back()=='\r')f.pop_back();
    if(f=="ticket_mask"){found=true;break;}
    if(end==std::string::npos)break;
    col++;pos=end+1;
  }
  if(!found)throw std::runtime_error("need ticket_mask column");
  std::vector<Draw> rows;std::string line;
  while(std::getline(in,line)){
    if(line.empty())continue;
    size_t start=0,end=std::string::npos;
    for(size_t k=0;k<=col;k++){
      end=line.find(',',start);
      if(k==col)break;
      if(end==std::string::npos)throw std::runtime_error("short row");
      start=end+1;
    }
    U64 mask=std::stoull(line.substr(start,end-start));
    rows.push_back({mask,mask?allowed_mask(mask):0u});
  }
  return rows;
}
static std::vector<Five> linear_forms(int n,int gap){
  std::vector<Five> forms(n);
  for(int bit=0;bit<64;bit++){
    U64 state=1ULL<<bit;
    for(int d=0;d<n;d++){
      U64 fourth=0;
      for(int i=0;i<5;i++){state=step(state);if(i==3)fourth=state;}
      for(int j=0;j<gap;j++)state=step(state);
      for(int k=0;k<5;k++)if((fourth>>(model.high?59+k:k))&1ULL)forms[d][k]|=1ULL<<bit;
    }
  }
  return forms;
}
struct Piv {U64 row=0;U128 expr=0;};
static int rank_of(const std::vector<Five>&f,const std::vector<int>&ids,int also=-1){
  U64 p[64]{};int rank=0;
  auto process=[&](int d){
    for(U64 x:f[d])while(x){
      int k=63-std::countl_zero(x);
      if(!p[k]){p[k]=x;rank++;break;}
      x^=p[k];
    }
  };
  for(int d:ids)process(d);
  if(also>=0)process(also);
  return rank;
}
static inline int parity(U128 n){
  return (__builtin_popcountll((U64)n)^__builtin_popcountll((U64)(n>>64)))&1;
}
struct Inverse {
  std::vector<std::array<U64,32>> seed;
  std::vector<std::array<U64,32>> synd;
  int rank=0;
  std::vector<U64> null_basis;
  bool build(const std::vector<Five>&f,const std::vector<int>&ids){
    int N=int(ids.size())*5;
    if(N>120)return false;
    Piv piv[64]{};std::vector<U128> deps;
    for(int i=0;i<N;i++){
      U64 x=f[ids[i/5]][i%5];U128 e=(U128)1<<i;
      while(x){
        int k=63-std::countl_zero(x);
        if(!piv[k].row){piv[k]={x,e};rank++;break;}
        x^=piv[k].row;e^=piv[k].expr;
      }
      if(!x)deps.push_back(e);
    }
    if(rank<60||deps.size()>63)return false;
    for(int free=0;free<64;free++)if(!piv[free].row){
      U64 state=1ULL<<free;
      for(int bit=0;bit<64;bit++)if(piv[bit].row){
        if(std::popcount(piv[bit].row&state)&1)state|=1ULL<<bit;
      }
      null_basis.push_back(state);
    }
    std::vector<U64> state_delta(N),syn_delta(N);
    for(int i=0;i<N;i++){
      U128 rhs=(U128)1<<i;
      U64 state=0,syn=0;
      for(int k=0;k<64;k++)if(piv[k].row){
        int bit=parity(piv[k].expr&rhs)^(std::popcount(piv[k].row&state)&1);
        if(bit)state|=1ULL<<k;
      }
      for(size_t k=0;k<deps.size();k++)if(parity(deps[k]&rhs))syn|=1ULL<<k;
      state_delta[i]=state;syn_delta[i]=syn;
    }
    seed.resize(ids.size());synd.resize(ids.size());
    for(size_t d=0;d<ids.size();d++)for(int val=0;val<32;val++){
      U64 state=0,syn=0;
      for(int k=0;k<5;k++)if((val>>k)&1){
        state^=state_delta[d*5+k];syn^=syn_delta[d*5+k];
      }
      seed[d][val]=state;synd[d][val]=syn;
    }
    return true;
  }
};
struct Engine{
  const std::vector<Draw>&data;
  const std::vector<Five>&forms;
  std::vector<int> indices,extra;
  Inverse inv;
  int gap=0,train_limit=0;
  U64 assignments=0,linear_consistent=0,domain_passed=0;
  U64 full_first=0,full_two=0,witness=0,exact_prefix=0;
  U64 bound=0;
  bool incomplete=false,found=false;
  explicit Engine(const std::vector<Draw>&d,const std::vector<Five>&f):data(d),forms(f){}
  void validate(U64 seed){
    for(int d:extra){
      uint32_t value=0;
      for(int k=0;k<5;k++)
        value|=(uint32_t(std::popcount(forms[d][k]&seed)&1)<<k);
      if((data[d].allowed&(1u<<value))==0)return;
    }
    domain_passed++;
    U64 state=seed;
    if(draw_ticket(state,gap)!=data[0].mask)return;
    full_first++;
    if(data.size()>1&&draw_ticket(state,gap)!=data[1].mask)return;
    full_two++;
    // Only training data are checked; withheld continuation is not consumed.
    for(int d=2;d<train_limit;d++){
      U64 produced=draw_ticket(state,gap);
      if(data[d].mask&&produced!=data[d].mask)return;
    }
    witness=seed;found=true;exact_prefix=train_limit;
  }
  void search(int depth,U64 seed,U64 syn){
    if(incomplete)return;
    if(depth==(int)indices.size()){
      if(++assignments>bound){incomplete=true;return;}
      if(syn==0){
        linear_consistent++;
        const U64 count=1ULL<<inv.null_basis.size();
        for(U64 mask=0;mask<count;mask++){
          U64 candidate=seed;
          for(size_t k=0;k<inv.null_basis.size();k++)
            if((mask>>k)&1ULL)candidate^=inv.null_basis[k];
          validate(candidate);
        }
      }
      return;
    }
    int d=indices[depth];uint32_t allowed=data[d].allowed;
    while(allowed){
      int v=std::countr_zero(allowed);allowed&=allowed-1;
      search(depth+1,seed^inv.seed[depth][v],syn^inv.synd[depth][v]);
      if(incomplete)return;
    }
  }
};
int main(int argc,char**argv){
  if(argc<4){
    std::cerr<<"usage: inverse64_branch DATA.csv TRAIN_LIMIT GAP [BRANCH_LIMIT] [EXTRA_CHECKS] [MAX_SELECTION_POOL] [A B C DIR HIGH]\n";
    return 2;
  }
  try{
    const auto start=std::chrono::steady_clock::now();
    auto data=read_csv(argv[1]);
    int train=std::stoi(argv[2]),gap=std::stoi(argv[3]);
    U64 branch_limit=argc>=5?std::stoull(argv[4]):20000000ULL;
    int extra_count=argc>=6?std::stoi(argv[5]):40;
    int pool_size=argc>=7?std::stoi(argv[6]):train;
    if(argc>=12){
      model.a=std::stoi(argv[7]);model.b=std::stoi(argv[8]);model.c=std::stoi(argv[9]);
      model.dir=std::stoi(argv[10]);model.high=std::stoi(argv[11]);
    }
    if(model.a<1||model.a>63||model.b<1||model.b>63||model.c<1||model.c>63||
       (model.dir!=0&&model.dir!=1)||(model.high!=0&&model.high!=1))
      throw std::runtime_error("invalid transition/sampler parameters");
    if(train<13||train>(int)data.size()||gap<0||gap>32||
       pool_size<13||pool_size>train||extra_count<0)
      throw std::runtime_error("invalid bounds");
    auto forms=linear_forms(train,gap);
    std::vector<int> ids;
    for(int i=0;i<pool_size;i++)if(data[i].mask)ids.push_back(i);
    if(data[0].mask==0||data[1].mask==0)
      throw std::runtime_error("first two tickets required");
    std::sort(ids.begin(),ids.end(),[&](int a,int b){
      int x=std::popcount(data[a].allowed),y=std::popcount(data[b].allowed);
      return x==y?a<b:x<y;
    });
    Engine e(data,forms);e.gap=gap;e.bound=branch_limit;e.train_limit=train;
    // Prefer twelve rank-five draws, then a rank-completing thirteenth.
    // Enumerate residual nullspace when the observation rank is under 64.
    int rank=0;
    std::vector<char> used(train);
    for(int d:ids){
      if(e.indices.size()>=12)break;
      int newrank=rank_of(forms,e.indices,d);
      if(newrank-rank==5){
        e.indices.push_back(d);used[d]=1;rank=newrank;
      }
    }
    if(e.indices.size()==12){
      for(int d:ids)if(!used[d]&&rank_of(forms,e.indices,d)==64){
        e.indices.push_back(d);used[d]=1;rank=64;break;
      }
    }
    while((e.indices.size()<13||rank<60)&&e.indices.size()<16){
      int best=-1,best_rank=rank;
      for(int d:ids)if(!used[d]){
        int nr=rank_of(forms,e.indices,d);
        if(nr>best_rank){best=d;best_rank=nr;}
      }
      if(best<0)break;
      e.indices.push_back(best);used[best]=1;rank=best_rank;
    }
    std::string status="UNKNOWN";
    if(rank>=60&&e.indices.size()>=13&&e.inv.build(forms,e.indices)){
      for(int d:ids)if(!used[d]&&(int)e.extra.size()<extra_count)
        e.extra.push_back(d);
      e.search(0,0,0);
      if(!e.incomplete){
        int observed=0;
        for(int d=0;d<train;d++)if(data[d].mask)observed++;
        status=e.found?(observed==train?"SAT":"SURVIVING"):"UNSAT";
      }
    }
    auto elapsed=std::chrono::duration<double>(
      std::chrono::steady_clock::now()-start).count();
    std::cout<<"{\"status\":\""<<status<<"\",\"rank\":"<<rank<<",\"selected\":[";
    for(size_t i=0;i<e.indices.size();i++)
      std::cout<<(i?",":"")<<e.indices[i];
    U128 product=1;
    for(int d:e.indices)product*=std::popcount(data[d].allowed);
    auto str128=[](U128 x){
      std::string s;
      do{s.push_back(char('0'+x%10));x/=10;}while(x);
      std::reverse(s.begin(),s.end());
      return s;
    };
    std::cout<<"],\"selection_domain_product\":\""<<str128(product)
      <<"\",\"assignments_examined\":"<<e.assignments
      <<",\"linear_consistent\":"<<e.linear_consistent
      <<",\"passed_extra_domains\":"<<e.domain_passed
      <<",\"matched_first\":"<<e.full_first
      <<",\"matched_second\":"<<e.full_two
      <<",\"witness_state\":"<<e.witness
      <<",\"full_ticket_prefix\":"<<e.exact_prefix
      <<",\"observed_training_rows\":"
      <<std::count_if(data.begin(),data.begin()+train,
        [](const Draw&x){return x.mask!=0;})
      <<",\"training_draws\":"<<train
      <<",\"total_draws\":"<<data.size()
      <<",\"branch_limit\":"<<branch_limit
      <<",\"seconds\":"<<elapsed<<"}\n";
    return 0;
  }catch(const std::exception &ex){
    std::cerr<<"error: "<<ex.what()<<"\n";
    return 2;
  }
}
