#define main replaced_joint_main
#include "joint_generator3d.cpp"
#undef main
int main(int argc,char **argv){
 try{if(argc!=2)throw runtime_error("usage: joint_smoke root");init();auto tr=read(string(argv[1])+"/train_labeled.csv",true);auto fut=read(string(argv[1])+"/future_features_only.csv",false);
  cout<<"gen,seed_rule,offset,sampler,permutation,draw_id,pred_perm_rank,n1,n2,n3,n4,n5\n";
  for(auto r:{tr.at(1),fut.at(0)}){
   for(int g=0;g<G;g++)for(int s=0;s<S;s++)for(int o=0;o<O;o++)for(int m=0;m<M;m++)for(int p=0;p<P;p++){
    auto [mask,per]=prediction({g,s,o,m,p},r);
    if(__builtin_popcountll(mask)!=5||per<0||per>=120)throw runtime_error("bad predicted event");
    cout<<gn[g]<<','<<sn[s]<<','<<offset[o]<<','<<mn[m]<<','<<pn[p]<<','<<r.id<<','<<per;
    for(int b=0;b<35;b++)if(mask&(1ULL<<b))cout<<','<<b+1;
    cout<<'\n';
   }
  }
 }catch(exception const&e){cerr<<"ERR "<<e.what()<<'\n';return 1;}
}
