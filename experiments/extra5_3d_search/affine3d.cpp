// 3-dimensional permutation inversion search: set/history X, time T, observed permutation P.
// Only train_labeled.csv has outcome labels; future_features_only.csv contains NO contemporaneous permutation.
// Exact exhaustive search over a,b,c in Z/120Z for each specified (X,T) pairing.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static constexpr int Q=120;
struct Row{int id,year,day,slot,setrank,sum,prevset,prevperm,prevsum,prev2,rank;};
vector<string> split(const string&s){vector<string>v;string z;stringstream ss(s);while(getline(ss,z,','))v.push_back(z);return v;}
vector<Row> read(const string &path,bool labels){
 ifstream f(path);if(!f)throw runtime_error("missing "+path);
 string line;getline(f,line);vector<string>h=split(line);vector<Row>result;
 auto get=[&](const vector<string>&r,const string&key,int def=-9){auto it=find(h.begin(),h.end(),key);return it==h.end()?def:stoi(r[it-h.begin()]);};
 while(getline(f,line)){if(line.empty())continue;auto r=split(line);result.push_back({get(r,"draw_id"),get(r,"year"),get(r,"date_ordinal"),get(r,"time_slot"),get(r,"set_rank"),get(r,"sum"),get(r,"prev_set_rank"),get(r,"prev_perm_rank"),get(r,"prev_sum"),get(r,"prev2_set_rank"),get(r,"perm_rank")});}
 return result;
}
int mod(int x){int r=x%Q;return r<0?r+Q:r;}
int xaxis(Row const&r,int x){switch(x){case 0:return r.setrank;case 1:return r.prevset;case 2:return r.prevperm;default:throw runtime_error("bad x axis");}}
int taxis(Row const&r,int t){return t==0?r.id:r.day;}
struct Winner{int x,t,a,b,c,train;};
int main(int argc,char **argv){
 try{
  if(argc!=2)throw runtime_error("usage: affine3d SEARCH_DIR");string dir=argv[1];
  auto tr=read(dir+"/train_labeled.csv",true), future=read(dir+"/future_features_only.csv",false);
  if(tr.size()!=2192||future.size()!=1334)throw runtime_error("wrong split");
  vector<Winner> winners;int maximum=-1;
  for(int x=0;x<3;x++)for(int t=0;t<2;t++){
   vector<int> xv(tr.size()),tv(tr.size()),yv(tr.size());
   for(size_t i=0;i<tr.size();i++){xv[i]=mod(xaxis(tr[i],x));tv[i]=mod(taxis(tr[i],t));yv[i]=mod(tr[i].rank);}
   Winner best{x,t,0,0,0,-1};
   for(int a=0;a<Q;a++){
    vector<uint8_t> ax(tr.size());for(size_t i=0;i<tr.size();i++)ax[i]=uint8_t((a*xv[i])%Q);
    for(int b=0;b<Q;b++){
     int count[Q]={0};
     for(size_t i=0;i<tr.size();i++){
      int c=int(yv[i])-int(ax[i])-b*tv[i];c=mod(c);count[c]++;
     }
     for(int c=0;c<Q;c++)if(count[c]>best.train){best={x,t,a,b,c,count[c]};}
    }
   }
   winners.push_back(best);maximum=max(maximum,best.train);
   cerr<<"group x="<<x<<" t="<<t<<" a="<<best.a<<" b="<<best.b<<" c="<<best.c<<" best train="<<best.train<<" / "<<tr.size()<<"\n";
  }
  ofstream lock(dir+"/FROZEN_AFFINE3D_models.csv");lock<<"family,x_axis,t_axis,a,b,c,train_exact,train_n\n";
  const char* X[] = {"current_set_rank_conditional", "previous_set_rank_forecast", "previous_permutation_forecast"};
  const char* T[] = {"draw_id", "date_ordinal"};
  for(auto&w:winners)lock<<"affine,"<<X[w.x]<<','<<T[w.t]<<','<<w.a<<','<<w.b<<','<<w.c<<','<<w.train<<','<<tr.size()<<'\n';
  ofstream pred(dir+"/FROZEN_AFFINE3D_future.csv");pred<<"draw_id,x_axis,t_axis,predicted_perm_rank\n";
  for(auto&w:winners)for(auto&r:future)
   pred<<r.id<<','<<X[w.x]<<','<<T[w.t]<<','<<mod(w.a*xaxis(r,w.x)+w.b*taxis(r,w.t)+w.c)<<'\n';
  cout<<"TOTAL_AFFINE_PARAMETER_TRIPLES="<<3*2*Q*Q*Q<<"\nPAIRS_FULLY_ENUMERATED="<<3*2*Q*Q<<"\nBEST_DEVELOPMENT_MATCHES="<<maximum<<'\n';
 }catch(exception const&e){cerr<<"ERROR "<<e.what()<<'\n';return 2;}
}
