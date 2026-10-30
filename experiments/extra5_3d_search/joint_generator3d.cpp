// EXTRA5 three-dimensional one-step next-draw generator laboratory.
// X = PREVIOUS winning set, Y = PREVIOUS recorded permutation, T = NEXT scheduled time.
// Each parameter tuple constructs an exact next SET and a relative-order PERMUTATION.
// Fit reads only train_labeled.csv. Forecast uses prior revealed information only.
// Models are hypotheses, not statements about the deployed RNG.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
using U=uint64_t;using V=uint32_t;
static constexpr U N=324632ULL,L32=(1ULL<<32)/N*N,L24=(1ULL<<24)/N*N;
static constexpr int G=8,S=14,O=9,M=5,P=4;
static const char* gn[]={"splitmix64","xorshift64star","pcg32","xoroshiro128plus","xoshiro256starstar","lcg64high","jsf32","xorshift32"};
static const char* sn[]={"prev_set","prev_perm","prev_set_perm","id_xor_prev_set","minute_xor_prev_set","id_xor_prev_perm","minute_xor_prev_perm","mixed_joint_id","mixed_joint_minute","mixed_lag2_id","prevsum_xor_minute","day_slot_prev_set","drawid_control","minute_control"};
static const char* mn[]={"rank32_rejection","rank24_rejection","fisher_mod","fisher_high","distinct_mod"};
static const char* pn[]={"same_stream_rank","same_stream_fisher","separate_stream_rank","sorted_control"};
static const int offset[]={-3600,-120,-60,-10,0,10,60,120,3600};
static U rotl(U x,int r){return (x<<r)|(x>>(64-r));}
static V rot32(V x,int r){return (x<<r)|(x>>(32-r));}
static U sm(U &s){U z=(s+=0x9e3779b97f4a7c15ULL);z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
struct RNG{
 int kind;U state,a=0,b=0,c=0,d=0;
 RNG(int k,U seed):kind(k),state(seed){
   if(k==1&&state==0)state=0x9e3779b97f4a7c15ULL;
   if(k==3){a=sm(state);b=sm(state);if(!(a|b))b=1;}
   if(k==4){a=sm(state);b=sm(state);c=sm(state);d=sm(state);if(!(a|b|c|d))d=1;}
   if(k==6){a=V(sm(state));b=V(sm(state));c=V(sm(state));d=V(sm(state));for(int j=0;j<20;j++)next();}
   if(k==7){state=V(state);if(!state)state=0x9e3779b9ULL;}
 }
 V next(){
  if(kind==0)return V(sm(state)>>32);
  if(kind==1){state^=state>>12;state^=state<<25;state^=state>>27;return V((state*2685821657736338717ULL)>>32);}
  if(kind==2){U old=state;state=old*6364136223846793005ULL+1442695040888963407ULL;V x=V(((old>>18)^old)>>27);int r=int(old>>59);return (x>>r)|(x<<((-r)&31));}
  if(kind==3){U s0=a,s1=b,res=s0+s1;s1^=s0;a=rotl(s0,55)^s1^(s1<<14);b=rotl(s1,36);return V(res>>32);}
  if(kind==4){U res=rotl(b*5,7)*9,t=b<<17;c^=a;d^=b;b^=c;a^=d;c^=t;d=rotl(d,45);return V(res>>32);}
  if(kind==5){state=6364136223846793005ULL*state+1442695040888963407ULL;return V(state>>32);}
  if(kind==6){V e=V(a)-rot32(V(b),27);a=V(V(b)^rot32(V(c),17));b=V(V(c)+V(d));c=V(V(d)+e);d=V(e+V(a));return V(d);}
  if(kind==7){V x=V(state);x^=x<<13;x^=x>>17;x^=x<<5;state=x;return x;}
  throw runtime_error("kind");
 }
};
static U comb(int n,int k){if(k<0||k>n)return 0;U v=1;for(int j=1;j<=k;j++)v=v*(n-k+j)/j;return v;}
static array<U,N> unrankmask{};
static void init(){
 for(int rank=0;rank<(int)N;rank++){
  int r=rank;U mask=0;int lower=1;
  for(int j=0;j<5;j++)for(int v=lower;v<=35;v++){
   int sub=int(comb(35-v,4-j));
   if(r<sub){mask|=(1ULL<<(v-1));lower=v+1;break;}r-=sub;
  }
  if(__builtin_popcountll(mask)!=5)throw runtime_error("bad unrank table");
  unrankmask[rank]=mask;
 }
}
struct R{int id,day,slot,curset,prevset,prevperm,prev2,prevsum,permr,year;U truth;};
vector<string> split(string const&s){vector<string>v;stringstream f(s);string w;while(getline(f,w,',')){if(!w.empty()&&w.back()=='\r')w.pop_back();v.push_back(w);}return v;}
vector<R> read(string path,bool truth){
 ifstream f(path);if(!f)throw runtime_error("cannot open "+path);string line;getline(f,line);vector<string>header=split(line);
 auto col=[&](string s){auto it=find(header.begin(),header.end(),s);return it==header.end()?-1:int(it-header.begin());};
 int id=col("draw_id"),day=col("date_ordinal"),slot=col("time_slot"),set=col("set_rank"),prev=col("prev_set_rank"),perm=col("prev_perm_rank"),prev2=col("prev2_set_rank"),sum=col("prev_sum"),year=col("year"),p=col("perm_rank");
 vector<R> rows;
 while(getline(f,line)){auto data=split(line);if(data.empty())continue;
  auto v=[&](int k){return k<0?-1:stoi(data[k]);};
  U mask=0;if(truth)for(int j=1;j<=5;j++){int k=col("n"+to_string(j));int n=v(k);if(n<1||n>35)throw runtime_error("bad draw");mask|=1ULL<<(n-1);}
  rows.push_back({v(id),v(day),v(slot),v(set),v(prev),v(perm),v(prev2),v(sum),v(p),v(year),mask});
 }
 return rows;
}
static U seed(R const&r,int rule,int of){
 U id=U(r.id),prev=U(r.prevset),pr=U(r.prevperm),prev2=U(r.prev2),day=U(r.day),minute=U(int64_t(r.day)-719163)*1440+U(r.slot?1140:900);
 U x=0;
 switch(rule){
  case 0:x=prev;break;
  case 1:x=pr;break;
  case 2:x=prev*120+pr;break;
  case 3:x=id^prev;break;
  case 4:x=minute^prev;break;
  case 5:x=id^pr;break;
  case 6:x=minute^pr;break;
  case 7:x=id^(prev<<17)^(pr<<51);x=sm(x);break;
  case 8:x=minute+prev*0x9e3779b97f4a7c15ULL+pr;x=sm(x);break;
  case 9:x=prev^(prev2<<1)^id;x=sm(x);break;
  case 10:x=U(r.prevsum)^minute;break;
  case 11:x=(day<<1)^U(r.slot)^prev;break;
  case 12:x=id;break;
  case 13:x=minute;break;
  default:throw runtime_error("seed rule");
 }
 return x+int64_t(of);
}
static U setgen(RNG &r,int method){
 if(method==0){for(int i=0;i<128;i++){U x=r.next();if(x<L32)return unrankmask[x%N];}return 0;}
 if(method==1){for(int i=0;i<128;i++){U x=r.next()>>8;if(x<L24)return unrankmask[x%N];}return 0;}
 if(method==4){U mask=0;for(int k=0;k<128&&__builtin_popcountll(mask)<5;k++)mask|=(1ULL<<(r.next()%35));return __builtin_popcountll(mask)==5?mask:0;}
 int a[35];iota(a,a+35,1);U mask=0;
 for(int i=0;i<5;i++){
  U r32=r.next();int bound=35-i;
  int v=method==2?int(r32%bound):int((r32*U(bound))>>32);
  swap(a[i],a[i+v]);mask|=1ULL<<(a[i]-1);
 }
 return mask;
}
static int permgen(RNG &r,int method,U initialseed){
 if(method==3)return 0;
 if(method==2){U x=initialseed^0x5045524d53485546ULL;x=sm(x);RNG other(r.kind,x);return permgen(other,0,initialseed);}
 if(method==0){const U limit=(1ULL<<32)/120*120;for(int i=0;i<128;i++){U n=r.next();if(n<limit)return int(n%120);}return -1;}
 int a[5]={0,1,2,3,4};
 for(int i=0;i<5;i++){int v=int(r.next()%(5-i));swap(a[i],a[i+v]);}
 int rank=0,remain[5]={0,1,2,3,4};for(int i=0;i<5;i++){int k=0;while(remain[k]!=a[i])k++;int facts[]={24,6,2,1,1};rank+=k*facts[i];for(int j=k;j<4-i;j++)remain[j]=remain[j+1];}
 if(rank<0||rank>119)throw runtime_error("permutation rank");
 return rank;
}
struct Config{int gen,rule,off,sm,pm;};
struct Score{int rare=0,hits=0,exact=0,perm=0,joint=0;};
static pair<U,int> prediction(Config c,R const&r){U v=seed(r,c.rule,offset[c.off]);RNG rng(c.gen,v);U set=setgen(rng,c.sm);int p=permgen(rng,c.pm,v);return {set,p};}
static string cstr(Config c){return string(gn[c.gen])+","+sn[c.rule]+","+to_string(offset[c.off])+","+mn[c.sm]+","+pn[c.pm];}
int main(int argc,char**argv){
 try{
  if(argc!=3)throw runtime_error("usage: joint_generator3d ROOT fit|forecast");string root=argv[1],mode=argv[2];init();
  if(mode=="fit"){
   auto rows=read(root+"/train_labeled.csv",true);if(rows.size()!=2192)throw runtime_error("bad training file");
   vector<Config> configs;vector<Score> scores;int best_rare=-1,best_hits=-1,best_joint=-1;
   for(int g=0;g<G;g++)for(int s=0;s<S;s++)for(int o=0;o<O;o++)for(int smm=0;smm<M;smm++)for(int pm=0;pm<P;pm++){
    Config conf{g,s,o,smm,pm};Score sc;
    for(size_t i=1;i<rows.size();i++){
     auto [mask,perm]=prediction(conf,rows[i]);
     int h=__builtin_popcountll(mask&rows[i].truth);sc.hits+=h;sc.rare+=(h>=4);sc.exact+=(h==5);
     sc.perm+=(perm==rows[i].permr);sc.joint+=(h>=4&&perm==rows[i].permr);
    }
    int id=int(configs.size());configs.push_back(conf);scores.push_back(sc);
    if(best_rare<0||sc.rare>scores[best_rare].rare||(sc.rare==scores[best_rare].rare&&sc.hits>scores[best_rare].hits))best_rare=id;
    if(best_hits<0||sc.hits>scores[best_hits].hits||(sc.hits==scores[best_hits].hits&&sc.rare>scores[best_hits].rare))best_hits=id;
    if(best_joint<0||sc.joint>scores[best_joint].joint||(sc.joint==scores[best_joint].joint&&sc.hits>scores[best_joint].hits))best_joint=id;
   }
   if(configs.size()!=size_t(G*S*O*M*P))throw runtime_error("library size");
   ofstream lock(root+"/FROZEN_JOINT3D_models.csv");lock<<"objective,gen,seed_rule,offset,sampler,permutation,train_4plus,train_total_hits,train_5plus,train_perm_correct,train_joint_4plus_correctperm\n";
   const char* tags[]={"rare4","overall_hits","joint4_order"};int chosen[]={best_rare,best_hits,best_joint};
   for(int k=0;k<3;k++){auto c=configs[chosen[k]];auto sc=scores[chosen[k]];
    lock<<tags[k]<<','<<cstr(c)<<','<<sc.rare<<','<<sc.hits<<','<<sc.exact<<','<<sc.perm<<','<<sc.joint<<'\n';
    cout<<tags[k]<<' '<<cstr(c)<<" rare4="<<sc.rare<<" hits="<<sc.hits<<" exact="<<sc.exact<<" perm="<<sc.perm<<" joint="<<sc.joint<<'\n';
   }
   cout<<"GENERATOR_CONFIGS="<<configs.size()<<" TRAIN_ONE_STEP_TARGETS="<<rows.size()-1<<"\n";
  }else if(mode=="forecast"){
   auto rows=read(root+"/future_features_only.csv",false);
   ifstream f(root+"/FROZEN_JOINT3D_models.csv");if(!f)throw runtime_error("LOCK REQUIRED");string line;getline(f,line);
   ofstream pred(root+"/FROZEN_JOINT3D_future.csv");pred<<"objective,draw_id,pred_perm_rank,n1,n2,n3,n4,n5\n";
   int k=0;while(getline(f,line)){
    auto fields=split(line);if(fields.size()<11)throw runtime_error("bad config line");
    Config c{};auto lookup=[&](const char*v,const char**choices,int n){for(int i=0;i<n;i++)if(string(choices[i])==v)return i;throw runtime_error("missing token "+string(v));};
    c.gen=lookup(fields[1].c_str(),gn,G);c.rule=lookup(fields[2].c_str(),sn,S);int off=stoi(fields[3]);for(int j=0;j<O;j++)if(offset[j]==off)c.off=j;
    c.sm=lookup(fields[4].c_str(),mn,M);c.pm=lookup(fields[5].c_str(),pn,P);
    for(auto const&r:rows){auto [mask,perm]=prediction(c,r);if(__builtin_popcountll(mask)!=5||perm<0||perm>=120)throw runtime_error("invalid prediction");
     pred<<fields[0]<<','<<r.id<<','<<perm;for(int bit=0;bit<35;bit++)if(mask&(1ULL<<bit))pred<<','<<bit+1;pred<<'\n';
    }
    k++;
   }
   if(k!=3)throw runtime_error("need 3 forecast arms");
   cout<<"FROZEN_JOINT_FORECASTS="<<k*rows.size()<<"\n";
  }else throw runtime_error("unknown mode");
 }catch(exception const&e){cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
